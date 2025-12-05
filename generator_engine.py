import requests  # 關鍵：使用 requests，不使用 google.generativeai
import re
import streamlit as st
import json

def configure_genai(api_key):
    # 只存 Key，不設定 SDK
    st.session_state.api_key_proxy = api_key

def generate_blueprint(product_idea):
    # 1. 取得 Key
    api_key = st.session_state.get("api_key_proxy", "")
    if not api_key:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")

    if not api_key:
        return {"error": "⚠️ API Key 遺失，請檢查 secrets.toml"}

    # 2. 設定 API (Gemini 1.5 Flash)
    model_name = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}

    # 3. 準備 Prompt
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

    data = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        # 4. 發送請求 (直接繞過 SDK)
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            return {"error": f"⚠️ Google 連線失敗 (Code {response.status_code}): {response.text}"}
        
        result_json = response.json()
        text_content = result_json['candidates'][0]['content']['parts'][0]['text']

        # 5. 切分檔案
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

        files["_model_used"] = "Gemini 1.5 Flash (REST API)"
        return files

    except Exception as e:
        return {"error": f"⚠️ 系統嚴重錯誤：{str(e)}"}
