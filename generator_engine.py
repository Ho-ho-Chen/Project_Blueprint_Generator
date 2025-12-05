import google.generativeai as genai
import re # 用來做正規表達式切割

def configure_genai(api_key):
    """設定 Gemini API"""
    genai.configure(api_key=api_key)

def generate_blueprint(product_idea):
    """
    呼叫 AI 生成四份標準化文件
    """
    # 使用支援較多 token 的模型，因為輸出內容會變長
    target_model = 'gemini-2.0-flash-exp' 
    
    try:
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
        
        response = model.generate_content(prompt)
        text = response.text
        
        # --- 解析 AI 回傳的文字，拆解成四個檔案 ---
        files = {}
        
        # 使用正規表達式抓取各個區塊
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
                files[filename] = f"⚠️ 生成內容遺失 ({filename})"

        return files

    except Exception as e:
        return {"error": f"⚠️ 系統錯誤：{str(e)}"}
