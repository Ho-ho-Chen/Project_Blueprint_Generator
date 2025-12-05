import google.generativeai as genai
import re
import time

def configure_genai(api_key):
    """設定 Gemini API"""
    genai.configure(api_key=api_key)

def generate_blueprint(product_idea):
    """
    呼叫 AI 生成四份標準化文件
    具備自動降級機制：如果 2.0 額度滿了，自動切換回 1.5 Flash
    """
    
    # 定義模型優先順序清單
    # 策略：先試試看最強的 2.0，如果失敗(429錯誤)，就換成穩定可靠的 1.5-flash
    model_priority = [
        'gemini-2.0-flash-exp',  # 優先嘗試：最新版 (額度少)
        'gemini-1.5-flash'       # 備案：穩定版 (額度高，速度快)
    ]
    
    last_error = ""

    for target_model in model_priority:
        try:
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

            # 成功就回傳結果，並標註是用哪個模型生成的
            files["_model_used"] = target_model 
            return files

        except Exception as e:
            last_error = str(e)
            # 如果是額度錯誤 (429) 或模型找不到，就繼續迴圈試下一個模型
            print(f"模型 {target_model} 失敗，嘗試下一個... 錯誤：{e}")
            continue

    # 如果所有模型都失敗
    return {"error": f"⚠️ 所有模型皆忙碌或額度不足。\n最後錯誤訊息：{last_error}"}
