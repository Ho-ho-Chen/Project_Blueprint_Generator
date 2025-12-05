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
# 👇 核心修復：模型人海戰術清單
# ==========================================
def call_gemini_api_robust(prompt_text, api_key):
    """
    策略：嘗試所有可能的模型名稱，直到成功為止。
    這能解決 404 (找不到模型) 與 429 (額度滿) 的所有問題。
    """
    # 定義模型優先順序 (包含最新的、最快的、最舊但最穩的)
    model_candidates = [
        "gemini-2.0-flash-exp",      # 首選：最新 2.0
        "gemini-1.5-flash",          # 次選：主流 1.5 Flash
        "gemini-1.5-flash-latest",   # 備選：Flash 最新別名
        "gemini-1.5-flash-001",      # 備選：Flash 固定版本
        "gemini-1.5-pro",            # 備選：1.5 Pro (比較慢但聰明)
        "gemini-1.5-pro-latest",     # 備選：Pro 最新別名
        "gemini-pro"                 # 保底：1.0 Pro (最舊但絕對存在，不死鳥)
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
            
            # 錯誤代碼處理
            error_msg = f"Error {response.status_code}: {response.text}"
            
            # 404 (找不到模型) 或 429 (額度滿) 或 503 (忙碌) -> 換下一個
            if response.status_code in [404, 429, 503]:
                print(f"⚠️ 模型 {model_name} 無法使用 ({response.status_code})，切換下一個...")
                time.sleep(0.5) # 稍微緩衝
                last_error = error_msg
                continue
            
            # 其他錯誤 (如 400 參數錯誤)
            last_error = error_msg
            
        except Exception as e:
            last_error = str(e)
            continue
            
    # 如果迴圈跑完都沒成功，拋出例外
    raise Exception(f"所有模型皆嘗試失敗。請檢查 API Key 是否正確。最後錯誤: {last_error}")

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
        # 3. 使用強固呼叫
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
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, content in files_dict.items():
            if not filename.startswith("_"): 
                zip_file.writestr(filename, content)
    return zip_buffer.getvalue()

def generate_structure(context_text):
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
    (請用 ASCII Tree 格式列出專案資料夾結構)

    ====FILE: FLOW.mermaid====
    (請寫一段 Mermaid JS 的 Sequence Diagram [序列圖] 代碼，開頭必須是 sequenceDiagram)
    """

    try:
        # 3. 使用強固呼叫
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
                content = content.replace("```mermaid", "").replace("```", "")
                result[k] = content
            else:
                result[k] = "生成失敗"
        return result

    except Exception as e:
        return {"STRUCTURE.txt": f"系統錯誤: {str(e)}", "FLOW.mermaid": ""}
