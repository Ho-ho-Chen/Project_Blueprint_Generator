import google.generativeai as genai
import re
import time
import streamlit as st

def configure_genai(api_key):
    """設定 Gemini API"""
    genai.configure(api_key=api_key)

def generate_blueprint(product_idea):
    """
    呼叫 AI 生成四份標準化文件
    具備自動降級機制：嘗試多種模型版本，直到成功為止。
    """
    
    # 定義模型優先順序清單 (由新到舊，由快到慢)
    # 策略：
    # 1. 2.0 Flash Exp: 最新、最強 (但也最容易額度滿)
    # 2. 1.5 Flash: 速度快、穩定
    # 3. 1.5 Pro: 比較聰明，但比較慢
    # 4. gemini-pro: 1.0 版本，最舊但通常絕對能用 (保底)
    model_priority = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    last_error = ""

    # 在介面上顯示我們正在做什麼
    status_placeholder = st.empty()

    for target_model in model_priority:
        try:
            status_placeholder.caption(f"🔄 正在嘗試連線模型：{target_model} ...")
            
            # 建立模型實例
            model = genai.GenerativeModel(target_model)
            
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
            
            # 發送請求
            response = model.generate_content(prompt)
            text = response.text
            
            # --- 解析 AI 回傳的文字 ---
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
                    files[filename] = f"⚠️ ({target_model}) 生成內容遺失，請重試。"

            # 成功！
            status_placeholder.success(f"✅ 成功使用模型：{target_model} 生成完畢！")
            time.sleep(1) # 讓使用者看到成功訊息
            status_placeholder.empty() # 清除訊息
            
            files["_model_used"] = target_model 
            return files

        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            print(f"❌ 模型 {target_model} 失敗: {error_msg}")
            
            # 判斷是否要稍微休息一下再試下一個 (避免連續請求被當作攻擊)
            if "429" in error_msg:
                status_placeholder.warning(f"⚠️ 模型 {target_model} 額度已滿，切換下一個...")
                time.sleep(2)
            else:
                status_placeholder.warning(f"⚠️ 模型 {target_model} 版本不支援，切換下一個...")
            
            continue

    # 如果所有模型都失敗
    return {"error": f"⚠️ 所有 AI 模型皆無法連線。\n建議：請在終端機執行 `python -m pip install -U google-generativeai` 更新套件。\n最後錯誤：{last_error}"}
