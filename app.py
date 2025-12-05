import streamlit as st
import generator_engine as engine
import config
import auth

# 1. 初始化頁面設定
config.setup_page()

# 2. 獲取機密資料
api_key, app_password = config.get_credentials()

# 3. 初始化登入狀態
auth.init_session_state()

# 4. 主流程控制
if not auth.is_logged_in():
    auth.login_page(app_password)
else:
    # 初始化 AI 引擎
    engine.configure_genai(api_key)
    
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("🔑 API Key 已自動載入")
        st.markdown("---")
        auth.logout_button()

    st.title("🏗️ AI 軟體架構師")
    st.markdown("#### 從點子到藍圖，生成全套工程文件")
    
    st.info("💡 輸入點子後，系統將自動產出：README, SPEC, Report, TodoList 四份標準文件。")

    product_idea = st.text_area(
        "你的產品點子是什麼？", 
        placeholder="例如：我想做一個專門給素食者的食譜分享 App...",
        height=150
    )

    if st.button("🚀 生成全套專案文件", type="primary"):
        if not product_idea:
            st.warning("請先輸入您的產品點子！")
        else:
            with st.spinner("🤖 架構師正在繪製藍圖、撰寫規格中... (可能需要約 30 秒)"):
                # 呼叫 engine 獲取字典格式的結果
                result_files = engine.generate_blueprint(product_idea)
                
                if "error" in result_files:
                    st.error(result_files["error"])
                else:
                    st.success("🎉 文件生成完畢！請查看下方頁籤。")
                    
                    # 建立四個頁籤
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📘 README.md", 
                        "⚙️ SPEC.md", 
                        "📊 REPORT.md", 
                        "✅ TODOLIST.md"
                    ])
                    
                    # --- Tab 1: README ---
                    with tab1:
                        content = result_files.get("README.md", "")
                        st.markdown(content)
                        st.download_button("下載 README.md", content, file_name="README.md")
                        
                    # --- Tab 2: SPEC (包含圖表) ---
                    with tab2:
                        content = result_files.get("SPEC.md", "")
                        st.markdown(content)
                        # 如果 AI 真的生成了 mermaid 代碼，Streamlit 其實無法直接渲染 markdown 裡的 mermaid
                        # 但如果 AI 用的是 ```mermaid 區塊，使用者閱讀上是沒問題的
                        st.download_button("下載 SPEC.md", content, file_name="SPEC.md")

                    # --- Tab 3: REPORT ---
                    with tab3:
                        content = result_files.get("REPORT.md", "")
                        st.markdown(content)
                        st.download_button("下載 REPORT.md", content, file_name="REPORT.md")

                    # --- Tab 4: TODOLIST ---
                    with tab4:
                        content = result_files.get("TODOLIST.md", "")
                        st.markdown(content)
                        st.download_button("下載 TODOLIST.md", content, file_name="TODOLIST.md")
