# ==========================================
# generator_engine.py: 核心邏輯與打包工具 (v2.4 Fix)
# ==========================================
import google.generativeai as genai
import json
import io
import zipfile
from config import ARCHITECT_PROMPT

def call_ai_architect(idea, api_key):
    """呼叫 AI 生成架構藍圖"""
    if not api_key: return None
    
    genai.configure(api_key=api_key)
    
    # 嘗試使用最強模型，若無則降級
    model = None
    try:
        # 嘗試連線 1.5-pro
        model = genai.GenerativeModel('gemini-1.5-pro')
        # 簡單測試連線
        model.generate_content("test")
    except:
        try:
            # 降級至 pro
            model = genai.GenerativeModel('gemini-pro')
        except:
            return {"error": "找不到可用的 Gemini 模型"}

    # 格式化 Prompt
    try:
        prompt = ARCHITECT_PROMPT.format(idea=idea)
    except Exception as e:
        return {"error": f"Prompt 格式化錯誤: {str(e)}"}
    
    try:
        response = model.generate_content(prompt)
        # 清洗 JSON (移除 Markdown 標記)
        json_str = response.text.strip()
        
        # 處理 ```json 包裹的情況
        if json_str.startswith("```json"):
            json_str = json_str.replace("```json", "", 1)
        elif json_str.startswith("```"):
            json_str = json_str.replace("```", "", 1)
            
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"AI 生成或解析錯誤: {str(e)}"}

def create_project_zip(data):
    """將 4 份文件打包成 ZIP"""
    
    # 錯誤處理：如果傳入的是錯誤訊息
    if "error" in data:
        return None

    # Helper: 安全地將資料轉為易讀的字串，避免格式錯誤
    def format_content(content, is_json=False):
        if not content:
            return ""
        if is_json:
            if isinstance(content, str):
                return content
            return json.dumps(content, indent=2, ensure_ascii=False)
        return str(content)

    # 1. README.md
    readme = f"""# {data.get('project_name', 'Project')}

## 📖 專案描述
{data.get('description', '')}

## 🎯 核心價值
{data.get('values', '')}

## 🛠️ 技術棧
{data.get('tech_stack', '')}
"""

    # 2. SPEC.md
    spec_content = format_content(data.get('structure_tree', ''), is_json=False)
    data_schema = format_content(data.get('data_schema', {}), is_json=True)
    
    # 注意：這裡使用了 f-string 內的換行，Python 3.6+ 支援
    spec = f"""# 📐 技術規格書

## 1. 系統架構圖
```text
{spec_content}
