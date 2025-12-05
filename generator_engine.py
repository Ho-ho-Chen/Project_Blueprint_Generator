import requests
import re
import streamlit as st
import json
import zipfile
import io
import time

def configure_genai(api_key):
    # 只存 Key，不設定 SDK
    st.session_state.api_key_proxy = api_key

def get_api_key():
    api_key = st.session_state.get("api_key_proxy", "")
    if not api_key:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
    return api_key

# ==========================================
# 👇 新增：強固型 API 呼叫函式 (處理 429 錯誤)
# ==========================================
def call_gemini_api_robust(prompt_text, api_key):
    """
    策略：優先使用 2.0-flash-exp，如果遇到 429 (額度滿) 或 503，
    自動切換到 1.5-flash (穩定版)。
    """
    # 定義模型優先順序
    model_candidates = [
        "gemini-2.0-flash-exp", 
        "gemini-1.5-flash"
    ]
    
    last_error = ""

    for model_name in model_candidates:
        # 建構該模型的 URL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt_text}]}]}
        
        try:
            # 發送請求
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # 如果成功 (200)，直接回傳 JSON 與使用的模型名稱
            if response.status_code == 200:
                return response.json(), model_name
            
            # 如果是 429 (額度滿) 或 503 (忙碌)，嘗試下一個模型
            if response.status_code in [429, 503]:
                print(f"⚠️ 模型 {model_name} 額度滿或忙碌，切換下一個...")
                time.sleep(1) # 稍微緩衝
                continue
            
            # 其他錯誤 (如 400 參數錯誤) 直接記錄，不繼續試
            last_error = f"Error {response.status_code}: {response.text}"
            
        except Exception as e:
            last_error = str(e)
            continue
            
    # 如果迴圈跑完都沒成功，拋出例外
    raise Exception(f"所有模型皆無法連線。最後錯誤: {last_error}")

# ==========================================
# 👇 主功能區
# ==========================================

def generate_blueprint(product_idea):
    # 1. 取得 Key
    api_key = get_api_key()
    if not api_key: return {"error": "⚠️ API Key 遺失，請檢查 secrets.toml"}

    # 2. 準備 Prompt
    prompt_text = f"""
    你是一位菁英軟體架構師。請根據以下專案需求，生成標準的軟體開發文件。
    
    {product_idea}

    【請嚴格依照以下格式輸出四個檔案區塊，不要有開場白】：
    
    ====FILE: README.md====
    (內容...)
    ====FILE: SPEC.md====
    (內容包含 Mermaid 圖表...)
    ====FILE: REPORT.md====
    (內容...)
    ====FILE: TODOLIST.md====
    (內容...)
    """

    try:
        # 3. 改用強固呼叫
        result_json, used_model = call_gemini_api_robust(prompt_text, api_key)
        
        text_content = result_json['candidates'][0]['content']['parts'][0]['text']

        # 4. 切分檔案
        files = {}
        patterns = {
            "README.md": r"====FILE: README\.md====\n(.*?)(?====FILE:|$)",
            "SPEC.md": r"====FILE: SPEC\.md====\n(.*?)(?====FILE:|$)",
            "REPORT.md": r"====FILE: REPORT\.md====\n(.*?)(?====FILE:|$)",
            "TODOLIST.md": r"====FILE: TODOLIST\.md====\n(.*?)(?====FILE:|$)",
        }
        
        for filename, pattern in patterns.items():
            match = re.search(pattern, text_content, re.DOTALL)
            files[filename] = match.group(1).strip() if match else f"⚠️ {filename} 生成遺失"

        # 標記實際使用的模型
        files["_model_used"] = f"{used_model} (Auto-Switch)"
        return files

    except Exception as e:
        return {"error": f"⚠️ 系統嚴重錯誤：{str(e)}"}

# ==========================================
# 👇 新增功能區 (ZIP & Structure)
# ==========================================

def create_zip_download(files_dict):
    """
    【新功能 1】將生成的字典檔案打包成 ZIP
    """
    zip_buffer = io.BytesIO()
    # 使用 ZIP_DEFLATED 壓縮算法
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, content in files_dict.items():
            # 忽略內部使用的標記欄位 (以 _ 開頭)
            if not filename.startswith("_"): 
                zip_file.writestr(filename, content)
    
    return zip_buffer.getvalue()

def generate_structure(context_text):
    """
    【新功能 2】Step 2: 根據上面的文件，生成檔案結構樹與流程圖
    """
    # 1. 取得 Key
    api_key = get_api_key()
    if not api_key: return {"STRUCTURE.txt": "API Key 遺失", "FLOW.mermaid": ""}

    # 2. 準備 Prompt
    prompt = f"""
    你是一位資深全端工程師。我們已經規劃好一份軟體規格：
    
    {context_text[:6000]} (擷取重點)
    
    請幫我設計這個專案的實體架構與運作流程。
    請嚴格依照以下格式輸出兩個區塊：

    ====FILE: STRUCTURE.txt====
    (請用 ASCII Tree 格式列出專案資料夾結構，例如：
    project_root/
    ├── frontend/
    │   └── package.json
    ├── backend/
    │   └── app.py
    )

    ====FILE: FLOW.mermaid====
    (請寫一段 Mermaid JS 的 Sequence Diagram [序列圖] 代碼，描述核心功能的運作閉環。
    開頭必須是 sequenceDiagram。
    不要包含 markdown 的 ``` 符號。
    )
    """

    try:
        # 3. 改用強固呼叫
        result_json, used_model = call_gemini_api_robust(prompt, api_key)
        
        text = result_json['candidates'][0]['content']['parts'][0]['text']
        
        # 4. 解析回傳
        result = {}
        patterns = {
            "STRUCTURE.txt": r"====FILE: STRUCTURE\.txt====\n(.*?)(?====FILE:|$)",
            "FLOW.mermaid": r"====FILE: FLOW\.mermaid====\n(.*?)(?====FILE:|$)",
        }
        for k, v in patterns.items():
            match = re.search(v, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # 清理可能多餘的 markdown 符號
                content = content.replace("```mermaid", "").replace("```", "")
                result[k] = content
            else:
                result[k] = "生成失敗"
                
        return result

    except Exception as e:
        return {"STRUCTURE.txt": f"系統錯誤: {str(e)}", "FLOW.mermaid": ""}
