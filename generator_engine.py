import requests  # 關鍵：使用 requests，不使用 google.generativeai
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
# 👇 核心修復：超級模型人海戰術
# ==========================================
def call_gemini_api_robust(prompt_text, api_key):
    """
    策略：依照「智力高 -> 速度快 -> 穩定舊版」的順序嘗試所有可用模型。
    只要其中任何一個能通，程式就會成功！
    """
    # 這是您帳號專屬的超級白名單 (依照推薦順序排列)
    model_candidates = [
        # --- Tier 1: 最強大腦 / 最新預覽 (優先嘗試) ---
        "gemini-3-pro-preview",
        "gemini-2.5-pro",
        "gemini-2.0-pro-exp-02-05",
        "gemini-2.0-pro-exp",
        "gemini-exp-1206",
        
        # --- Tier 2: 極速與平衡 (Flash 系列) ---
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp", # 許多新功能都在這
        "gemini-1.5-flash",     # 最穩定且額度高
        "gemini-flash-latest",
        
        # --- Tier 3: 輕量版 (Lite) ---
        "gemini-2.0-flash-lite-preview-02-05",
        "gemini-2.5-flash-lite",
        
        # --- Tier 4: 保底舊版 (不死鳥) ---
        "gemini-1.5-pro",
        "gemini-pro"
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
                # 成功了！告訴前端是哪個模型立大功
                return response.json(), model_name
            
            # 錯誤代碼處理
            error_msg = f"Error {response.status_code}: {response.text}"
            
            # 404 (找不到), 429 (額度滿), 503 (忙碌) -> 換下一個
            if response.status_code in [404, 429, 503]:
                # 在後台印出訊息方便除錯 (Streamlit 介面不會顯示，保持乾淨)
                print(f"⚠️ 模型 {model_name} 跳過 ({response.status_code})")
                time.sleep(0.2) # 極短暫緩衝
                last_error = error_msg
                continue
            
            # 其他錯誤 (如 400 參數錯誤)
            last_error = error_msg
            
        except Exception as e:
            last_error = str(e)
            continue
            
    # 如果幾十個模型全部失敗 (機率極低)，才拋出例外
    raise Exception(f"所有 {len(model_candidates)} 個模型皆嘗試失敗。請檢查 API Key 權限。最後錯誤: {last_error}")

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
        files["_model_used"] = f"{used_model}"
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
