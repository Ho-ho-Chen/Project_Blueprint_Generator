import requests
import re
import streamlit as st
import json
import zipfile
import io
import time

def configure_genai(api_key):
    st.session_state.api_key_proxy = api_key

def get_api_key():
    api_key = st.session_state.get("api_key_proxy", "")
    if not api_key:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
    return api_key

# ==========================================
# 👇 核心修復：整合超級模型白名單 (確保連線成功率)
# ==========================================
def call_gemini_api_robust(prompt_text, api_key):
    """
    策略：依照「智力高 -> 速度快 -> 穩定備用」的順序嘗試所有可用模型。
    只要清單中任何一個能通，程式就會成功！
    """
    # 這是根據您 Colab 查詢結果整理的超級白名單
    model_candidates = [
        # --- Tier 1: 神級模型 (最新最強，優先嘗試) ---
        "gemini-3-pro-preview",
        "gemini-2.5-pro",
        "gemini-2.5-pro-preview-tts",
        
        # --- Tier 2: 2.0 強力實驗版 ---
        "gemini-2.0-pro-exp-02-05",
        "gemini-2.0-pro-exp",
        "gemini-exp-1206",
        
        # --- Tier 3: 極速 Flash 系列 (速度快、額度較高) ---
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp", 
        "gemini-2.0-flash-001",
        "gemini-flash-latest",
        
        # --- Tier 4: 輕量版 (Lite & Gemma) ---
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite-preview-02-05",
        "gemma-3-27b-it", # Google 最強開源模型
        
        # --- Tier 5: 保底舊版 (最後防線) ---
        "gemini-pro-latest",
        "gemini-pro"
    ]

    last_error = ""
    for model_name in model_candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt_text}]}]}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # 成功回傳
            if response.status_code == 200:
                return response.json(), model_name
            
            # 遇到 404/429/503 就換下一個
            if response.status_code in [404, 429, 503]:
                # print(f"⚠️ 模型 {model_name} 跳過 ({response.status_code})") # 除錯用
                time.sleep(0.1)
                continue
                
            last_error = f"Error {response.status_code}: {response.text}"
            
        except Exception as e:
            last_error = str(e)
            continue
            
    raise Exception(f"所有 {len(model_candidates)} 個模型皆嘗試失敗。最後錯誤: {last_error}")

# ==========================================
# 👇 功能 1: AI 需求分析師 (生成問卷)
# ==========================================
def generate_interview_questions(project_name, project_desc):
    """
    根據用戶模糊的描述，生成 3 個引導式問題
    """
    api_key = get_api_key()
    if not api_key: return {"error": "API Key 遺失"}

    prompt = f"""
    你是一位資深產品經理。使用者想要開發一個軟體，但他只知道大概的想法。
    
    專案名稱：{project_name}
    初步構想：{project_desc}
    
    請針對這個構想，提出 3 個關鍵的技術或功能問題，用來釐清規格。
    問題方向請涵蓋：
    1. 前端互動 (User Interface)
    2. 後端邏輯 (Business Logic)
    3. 資料儲存 (Data)
    
    請務必使用「繁體中文」提問，問題要簡單易懂，適合新手回答。
    
    【請嚴格依照 JSON 格式輸出，不要有 Markdown 標記】：
    {{
        "q_frontend": "你的前端問題...",
        "q_backend": "你的後端問題...",
        "q_database": "你的資料庫問題..."
    }}
    """
    
    try:
        res_json, _ = call_gemini_api_robust(prompt, api_key)
        text = res_json['candidates'][0]['content']['parts'][0]['text']
        # 清理 JSON 字串 (避免 AI 加上 ```json ...)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": f"問卷生成失敗: {str(e)}"}

# ==========================================
# 👇 功能 2: 生成藍圖 (雙語版)
# ==========================================
def generate_blueprint(full_requirements):
    api_key = get_api_key()
    if not api_key: return {"error": "API Key 遺失"}

    prompt_text = f"""
    你是一位菁英軟體架構師。請根據以下完整的訪談需求，生成標準的軟體開發文件。
    
    【需求訪談紀錄】：
    {full_requirements}

    【輸出要求】：
    1. **請務必使用「繁體中文 (Traditional Chinese) + 英文 (English)」雙語對照。**
    2. 內容需包含：README, SPEC, REPORT, TODOLIST。
    
    【請嚴格依照以下格式輸出四個檔案區塊】：
    ====FILE: README.md====
    (內容...)
    ====FILE: SPEC.md====
    (內容包含 Mermaid...)
    ====FILE: REPORT.md====
    (內容...)
    ====FILE: TODOLIST.md====
    (內容...)
    """
    
    try:
        res_json, model = call_gemini_api_robust(prompt_text, api_key)
        text = res_json['candidates'][0]['content']['parts'][0]['text']
        
        files = {}
        patterns = {
            "README.md": r"====FILE: README\.md====\n(.*?)(?====FILE:|$)",
            "SPEC.md": r"====FILE: SPEC\.md====\n(.*?)(?====FILE:|$)",
            "REPORT.md": r"====FILE: REPORT\.md====\n(.*?)(?====FILE:|$)",
            "TODOLIST.md": r"====FILE: TODOLIST\.md====\n(.*?)(?====FILE:|$)",
        }
        for k, v in patterns.items():
            match = re.search(v, text, re.DOTALL)
            files[k] = match.group(1).strip() if match else f"⚠️ {k} 生成遺失"
            
        files["_model_used"] = model
        return files
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 👇 功能 3: 生成結構圖 (雙語版)
# ==========================================
def generate_structure(context_text):
    api_key = get_api_key()
    if not api_key: return {"STRUCTURE.txt": "Key Error", "FLOW.mermaid": ""}

    prompt = f"""
    你是一位資深全端工程師。根據以下規格：
    {context_text[:6000]}
    
    請設計實體架構與運作流程。
    請務必使用「繁體中文 + 英文」雙語進行資料夾結構的註解說明。
    
    格式要求：
    ====FILE: STRUCTURE.txt====
    (ASCII Tree)
    ====FILE: FLOW.mermaid====
    (Mermaid sequenceDiagram)
    """
    
    try:
        res_json, _ = call_gemini_api_robust(prompt, api_key)
        text = res_json['candidates'][0]['content']['parts'][0]['text']
        result = {}
        patterns = {
            "STRUCTURE.txt": r"====FILE: STRUCTURE\.txt====\n(.*?)(?====FILE:|$)",
            "FLOW.mermaid": r"====FILE: FLOW\.mermaid====\n(.*?)(?====FILE:|$)",
        }
        for k, v in patterns.items():
            match = re.search(v, text, re.DOTALL)
            if match:
                result[k] = match.group(1).strip().replace("```mermaid", "").replace("```", "")
            else:
                result[k] = "生成失敗"
        return result
    except Exception as e:
        return {"STRUCTURE.txt": f"Error: {e}", "FLOW.mermaid": ""}

# ==========================================
# 👇 功能 4: 下載打包
# ==========================================
def create_zip_download(files_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, content in files_dict.items():
            if not filename.startswith("_"): 
                zip_file.writestr(filename, content)
    return zip_buffer.getvalue()
