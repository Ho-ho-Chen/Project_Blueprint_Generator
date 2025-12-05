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

# --- 核心：強固型連線 ---
def call_gemini_api_robust(prompt_text, api_key):
    model_candidates = [
        "gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"
    ]
    last_error = ""
    for model_name in model_candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt_text}]}]}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                return response.json(), model_name
            if response.status_code in [404, 429, 503]:
                time.sleep(0.5)
                continue
            last_error = f"Error {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)
            continue
    raise Exception(f"所有模型皆失敗。最後錯誤: {last_error}")

# --- 新功能：AI 需求分析師 (生成問卷) ---
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
        # 清理 JSON 字串
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": f"問卷生成失敗: {str(e)}"}

# --- 原有功能：生成藍圖 ---
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

# --- 原有功能：生成結構圖 ---
def generate_structure(context_text):
    api_key = get_api_key()
    if not api_key: return {"STRUCTURE.txt": "Key Error", "FLOW.mermaid": ""}

    prompt = f"""
    你是一位資深全端工程師。根據以下規格：
    {context_text[:6000]}
    
    請設計實體架構與運作流程 (雙語註解)。
    
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

# --- 下載打包功能 ---
def create_zip_download(files_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, content in files_dict.items():
            if not filename.startswith("_"): 
                zip_file.writestr(filename, content)
    return zip_buffer.getvalue()
