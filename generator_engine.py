# ==========================================
# generator_engine.py: 核心邏輯與打包工具 (v2.4)
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
    try:
        # 嘗試連線 1.5-pro
        model = genai.GenerativeModel('gemini-1.5-pro')
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
        if json_str.startswith("```json"):
            json_str = json_str.replace("```json", "", 1)
        if json_str.startswith("```"):
            json_str = json_str.replace("```", "", 1)
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"AI 生成或解析錯誤: {str(e)}"}

def create_project_zip(data):
    """將 4 份文件打包成 ZIP"""
    
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
    # 注意：將 list 或 dict 轉為字串，避免 f-string 報錯
    spec_content = data.get('structure_tree', '')
    data_schema = str(data.get('data_schema', '{}'))
    
    spec = f"""# 📐 技術規格書

## 1. 系統架構圖
```text
{spec_content}
````

## 2\. 資料結構 (Data Schema)

```json
{data_schema}
```

"""

```
# 3. TODOLIST.md
todo_p1 = data.get('todo_phase1', '')
todo_p2 = data.get('todo_phase2', '')

todo = f"""# ✅ 任務清單
```

## Phase 1: MVP (最小可行性產品)

{todo\_p1}

## Phase 2: Scale (擴充階段)

{todo\_p2}
"""

```
# 4. REPORT.md
risk_log = data.get('risk_log', '')

report = f"""# 📋 開發日誌 (Dev Report)
```

## 初始評估與風險

{risk\_log}
"""

```
# 執行打包動作
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("README.md", readme)
    z.writestr("SPEC.md", spec)
    z.writestr("TODOLIST.md", todo)
    z.writestr("REPORT.md", report)

buffer.seek(0)
return buffer
```

```
```
