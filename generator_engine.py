import google.generativeai as genai
import streamlit as st

def configure_genai(api_key):
    """設定 Gemini API"""
    genai.configure(api_key=api_key)

def generate_blueprint(product_idea):
    """
    呼叫 AI 生成架構藍圖
    Args:
        product_idea: 使用者輸入的點子
    Returns:
        response text (Markdown)
    """
    # 這裡可以選擇模型，flash 速度快便宜，pro 能力強
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 可以在這裡優化您的 Prompt (提示詞)
    prompt = f"""
    你是一位資深的軟體架構師。請根據以下產品點子，生成一份專業的軟體架構藍圖。
    
    【使用者需求】：
    {product_idea}
    
    【請輸出以下內容 (使用 Markdown 格式)】：
    1. **核心功能清單 (Core Features)**：列出 3-5 個關鍵功能點。
    2. **資料庫結構 (Data Schema)**：建議的資料表 (Table) 與欄位。
    3. **技術棧推薦 (Tech Stack)**：前端、後端、資料庫的建議選擇。
    4. **開發階段規劃 (Roadmap)**：MVP 開發順序。
    
    請用繁體中文回答，語氣專業且條理分明。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 生成失敗，API 錯誤訊息：{str(e)}"
