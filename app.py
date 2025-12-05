import streamlit as st
import config
import auth
import generator_engine as engine

# 1. 初始化頁面設定
config.setup_page()

# 2. 獲取機密資料 (Key 和 Password)
api_key, app_password = config.get_credentials()

# 3. 初始化登入狀態
auth.init_session_state()

# 4. 主流程控制
if not auth.is_logged_in():
    # --- 情境 A：未登入 ---
    auth.login_page(app_password)
    
else:
    # --- 情境 B：已登入 (顯示主程式) ---
    
    # 初始化 AI 引擎
    engine.configure_genai(api_key)
    
    # 側邊欄
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("🔑 API Key 已由系統自動載入")
        st.markdown("---")
        auth.logout_button() # 呼叫登出功能

    # 主畫面
    st.title("🏗️ AI 軟體架構師")
    st.markdown("#### 從點子到藍圖，只要一瞬間")

    product_idea = st.text_area(
        "你的產品點子是什麼？", 
        placeholder="例如：我想做一個專門給素食者的食譜分享 App...",
        height=150
    )

    if st.button("🚀 開始生成架構藍圖", type="primary"):
        if not product_idea:
            st.warning("請先輸入您的產品點子！")
        else:
            with st.spinner("🤖 AI 架構師正在思考中..."):
                # 呼叫 engine 生成內容
                result = engine.generate_blueprint(product_idea)
                
                # 顯示結果
                st.markdown("---")
                st.subheader("📄 生成結果")
                st.markdown(result)
