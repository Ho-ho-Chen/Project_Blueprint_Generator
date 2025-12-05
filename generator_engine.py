# ==========================================
# generator_engine.py: 核心邏輯
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
    # 嘗試使用最強模型
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
    except:
        model = genai.GenerativeModel('gemini-pro')

    prompt = ARCHITECT_PROMPT.format(idea=idea)
    
    try:
        response = model.generate_content(prompt)
        # 清洗 JSON
        json_str = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_str)
    except Exception as e:
        return {"error": str(e)}

def create_project_zip(data):
    """將 4 份文件打包成 ZIP"""
    
    # 1. README.md
    readme = f"""# {data.get('project_name')}
    
## 📖 專案描述
{data.get('description')}

## 🎯 核心價值
{data.get('values')}

## 🛠️ 技術棧
{data.get('tech_stack')}
"""

    # 2. SPEC.md
    spec = f"""# 📐 技術規格書

## 1. 系統架構圖
```text
{data.get('structure_tree')}
