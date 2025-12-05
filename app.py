import streamlit as st
import google.generativeai as genai

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="AI 軟體架構師",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 登入系統邏輯 (守門員) ---
# 初始化 session state 來紀錄登入狀態
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_password():
    """比對使用者輸入的密碼與 secrets 中的密碼"""
    # 讀取 secrets 中的密碼，如果沒設定則預設為空
    stored_password = st.secrets.get("app_password", "")
    
    if st.session_state.password_input == stored_password:
        st.session_state.logged_in = True
        del st.session_state.password_input  # 登入成功後清除暫存
    else:
        st.error("❌ 密碼錯誤，請重新輸入。")

# --- 3. 介面控制流程 ---

# [情境 A]：還沒登入 -> 顯示登入畫面
if not st.session_state.logged_in:
    st.markdown("## 🔒 系統鎖定中")
    st.markdown("請輸入授權密碼以存取 **AI 軟體架構師** 工具。")
    
    st.text_input(
        "訪問密碼：", 
        type="password", 
        key="password_input", 
        on_change=check_password
    )
    
    st.markdown("---")
    st.caption("© 2025 AI 軟體架構師 | 僅限授權人員使用")

# [情境 B]：已經登入 -> 顯示完整功能
else:
    # --- 自動讀取 API Key ---
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # 設定 Gemini
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error("⚠️ 系統錯誤：找不到 API Key，請檢查 secrets.toml 設定。")
        st.stop()

    # --- 側邊欄 (功能選單) ---
    with st.sidebar:
        st.success(f"✅ 歡迎回來，老師！")
        st.info("🔑 API Key 已安全載入")
        
        st.markdown("---")
        if st.button("🚪 登出系統"):
            st.session_state.logged_in = False
            st.rerun() # 重新整理頁面回到登入畫面

    # --- 主畫面內容 ---
    st.title("🏗️ AI 軟體架構師")
    st.markdown("#### 從點子到藍圖，只要一瞬間")
    
    st.info("💡 這個工具會根據您的需求，自動生成軟體規格書、資料結構與開發清單。")

    # 輸入區
    product_idea = st.text_area(
        "你的產品點子是什麼？", 
        placeholder="例如：我想做一個專門給素食者的食譜分享 App，要有地圖功能、不含蛋奶的篩選器...",
        height=150
    )

    # 執行按鈕
    if st.button("🚀 開始生成架構藍圖", type="primary"):
        if not product_idea:
            st.warning("請先輸入您的產品點子！")
        else:
            with st.spinner("🤖 AI 架構師正在思考中，請稍候..."):
                try:
                    # 設定 AI 模型 (使用 Gemini Pro)
                    model = genai.GenerativeModel('gemini-1.5-flash') # 或使用 gemini-pro
                    
                    # 設計 Prompt (提示詞)
                    prompt = f"""
                    你是一位資深的軟體架構師。請根據以下產品點子，生成一份專業的架構藍圖。
                    請包含：1. 核心功能條列 2. 資料庫結構建議 3. 技術棧推薦 4. 開發階段規劃。
                    
                    產品點子：{product_idea}
                    請用繁體中文回答，使用 Markdown 格式。
                    """
                    
                    # 發送請求
                    response = model.generate_content(prompt)
                    
                    # 顯示結果
                    st.markdown("---")
                    st.markdown("### 📄 生成結果")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"生成失敗，請檢查連線或額度。\n錯誤訊息：{e}")
