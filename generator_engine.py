import requests
import json
import re
import streamlit as st

# 全域變數用來暫存 Key
_API_KEY = None

def configure_genai(api_key):
    """
    設定 API Key
    注意：這裡我們只把 Key 存起來，不呼叫 genai.configure，避免觸發舊版套件錯誤
    """
    global _API_KEY
    _API_KEY = api_key

def generate_blueprint(product_idea):
    """
    使用原始 HTTP 請求 (REST API) 呼叫 Gemini
    這種方式不依賴 google-generativeai 套件的版本，解決 404/Version 錯誤
    """
    global _API_KEY
    
    if not _API_KEY:
        return {"error": "⚠️ API Key 未設定，請重新登入。"}

    # 使用 Gemini 1.5 Flash 模型 (速度快、穩定)
    # 直接對 Google 的網址發送請求，就像瀏覽器一樣
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={_API_KEY}"
    
    headers = {
        'Content-Type': 'application/json'
    }

    # 這是我們要傳給 AI 的指令
    prompt = f"""
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

    # 準備資料包裹
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        # 發射！直接發送 POST 請求
        response = requests.post(url, headers=headers, json=payload)
        
        # 檢查是否有網路錯誤
        if response.status_code != 200:
            return {"error": f"⚠️ 連線失敗 (代碼 {response.status_code})：\n{response.text}"}
            
        # 解析回傳的 JSON 資料
        result = response.json()
        
        # 嘗試取得生成的文字
        try:
            text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return {"error": "⚠️ 生成失敗，Google 回傳了非預期的格式。"}

        # --- 解析 AI 回傳的文字，拆解成四個檔案 ---
        files = {}
        files["_model_used"] = "gemini-1.5-flash (REST API)" # 標記我們用了這個方法
        
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
                # 簡單容錯：如果沒抓到，就給個提示
                files[filename] = f"⚠️ ({filename}) 內容解析失敗，請再試一次。"

        return files

    except Exception as e:
        return {"error": f"⚠️ 系統發生未預期的錯誤：{str(e)}"}
