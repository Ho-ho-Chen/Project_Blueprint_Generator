import google.generativeai as genai
import json
import io
import zipfile
from config import ARCHITECT_PROMPT

def call_ai_architect(idea, api_key):
    if not api_key:
        return None
    
    genai.configure(api_key=api_key)
    
    model = None
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        model.generate_content("test")
    except:
        try:
            model = genai.GenerativeModel('gemini-pro')
        except:
            return {"error": "找不到可用的 Gemini 模型"}

    try:
        prompt = ARCHITECT_PROMPT.format(idea=idea)
    except Exception as e:
        return {"error": f"Prompt 格式化錯誤: {str(e)}"}
    
    try:
        response = model.generate_content(prompt)
        json_str = response.text.strip()
        
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
    if "error" in data:
        return None

    def format_content(content, is_json=False):
        if not content:
            return ""
        if is_json:
            if isinstance(content, str):
                return content
            return json.dumps(content, indent=2, ensure_ascii=False)
        return str(content)

    readme = f"""# {data.get('project_name', 'Project')}

## 專案描述
{data.get('description', '')}

## 核心價值
{data.get('values', '')}

## 技術棧
{data.get('tech_stack', '')}
"""

    spec_content = format_content(data.get('structure_tree', ''), is_json=False)
    data_schema = format_content(data.get('data_schema', {}), is_json=True)
    
    spec = f"""# 技術規格書

## 1. 系統架構圖
{spec_content}

## 2. 資料結構 (Data Schema)
{data_schema}
"""

    todo_p1 = format_content(data.get('todo_phase1', ''))
    todo_p2 = format_content(data.get('todo_phase2', ''))

    todo = f"""# 任務清單

## Phase 1: MVP
{todo_p1}

## Phase 2: Scale
{todo_p2}
"""

    risk_log = format_content(data.get('risk_log', ''))

    report = f"""# 開發日誌

## 初始評估與風險
{risk_log}
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.md", readme)
        z.writestr("SPEC.md", spec)
        z.writestr("TODOLIST.md", todo)
        z.writestr("REPORT.md", report)

    buffer.seek(0)
    return buffer
