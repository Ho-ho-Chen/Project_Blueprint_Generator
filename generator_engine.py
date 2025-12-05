import requests # 改用標準網頁請求，不依賴 Google SDK
import re
import json
import streamlit as st

def configure_genai(api_key):
    """
    因為改用 direct REST API，這裡不需要做 SDK 的設定，
    但為了保持 app.py 不用改，我們保留這個函式，存下 key 即可。
    """
    st.session_state.api_key_proxy = api_key

def generate_blueprint(product_idea):
    """
    使用 Requests 直接呼叫 Google Gemini API (REST 方式)
    這能避開 SDK 版本過舊的問題。
    """
    
    # 從 session 讀取 key
    api_key = st.session_state.get("api_key_proxy", "")
    if not api_key:
        return {"error": "⚠️ API Key 遺失，請重新登入。"}

    # 使用 Gemini 1.5 Flash (目前最穩定快速且免費額度高)
    model_name = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    # 建構 Header
    headers = {
        "Content-Type": "application/json"
    }

    # 建構 Prompt
    prompt_text = f"""
    你是一位菁英軟體架構師。請根據使用者的產品點子，生成一個完整的軟體專案文件包。
    你需要生成以下四個檔案的內容，並用特定的分隔線隔開。
    
    【產品點子】：
    {product_idea}

    【請嚴格依照以下格式輸出，不要包含其他開場白】：

    ====FILE: README.md====
    (在此撰寫 README.md 的內容：專案標題、描述、安裝指南、技術棧清單)

    ====FILE: SPEC.md====
    (在此撰寫 SPEC.md 的內容：詳細規格、API 端點定義。請包含至少一個 Mermaid 格式的系統架構圖或是流程圖)

    ====FILE: REPORT.md====
    (在此撰寫 REPORT.md 的內容：開發評估報告、預期遇到的技術難點、解決方案分析)

    ====FILE: TODOLIST.md====
    (在此撰寫 TODOLIST.md 的內容：條列式開發任務清單，包含 Checkbox - [ ])
    """

    # 建構 JSON Body
    data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        # 發送 POST 請求
        response = requests.post(url, headers=headers, json=data)
        
        # 檢查回應狀態
        if response.status_code != 200:
            error_detail = response.text
            return {"error": f"⚠️ Google API 連線失敗 (Code {response.status_code})。\n詳細原因：{error_detail}"}
        
        # 解析 JSON
        result_json = response.json()
        
        try:
            # 取得生成的文字
            text = result_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return {"error": "⚠️ 生成失敗，回傳資料格式不如預期。可能內容被阻擋。"}

        # --- 解析 AI 回傳的文字，拆解成四個檔案 ---
        files = {}
        patterns = {
            "README.md": r"====FILE: README\.md====\n(.*?)(?====FILE:|$)",
            "SPEC.md": r"====FILE: SPEC\.md====\n(.*?)(?====FILE:|$)",
            "REPORT.md": r"====FILE: REPORT\.md====\n(.*?)(?====FILE:|$)",
            "TODOLIST.md": r"====FILE: TODOLIST\.md====\n(.*?)(?====FILE:|$)",
        }
        
        for filename, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                files[filename] = match.group(1).strip()
            else:
                files[filename] = f"⚠️ 內容遺失 ({filename})"

        files["_model_used"] = f"{model_name} (REST API)"
        return files

    except Exception as e:
        return {"error": f"⚠️ 系統嚴重錯誤：{str(e)}"}
