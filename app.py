import streamlit as st
import config
import auth
import generator_engine as engine

# --- 1. 初始化與登入 ---
config.setup_page()
api_key, app_password = config.get_credentials()
auth.init_session_state()

if not auth.is_logged_in():
    auth.login_page(app_password)
else:
    # 這裡我們只傳遞 Key，不做 SDK 設定 (因為我們要改用 REST API)
    engine.configure_genai(api_key)
    
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("💡 連線模式：HTTP 直連 (已繞過版本限制)")
        st.markdown("---")
        auth.logout_button()

    st.title("🏗️ PolyGlot 架構生成器")
    st.markdown("#### 分段輸入構想，生成標準工程文件")
    st.info("請依照下方引導填寫需求，系統將為您生成 README, SPEC, Report 與 Todo List。")

    # --- 改為分段式表單設計 ---
    with st.form("project_input_form"):
        
        st.subheader("1. 專案基本資訊")
        col1, col2 = st.columns([1, 2])
        project_name = col1.text_input("專案名稱", value="PolyGlotBook AI")
        project_desc = col2.text_input("一句話描述", value="一站式生成雙語對照、有聲朗讀 EPUB3 的 SaaS 平台")

        st.markdown("---")
        st.subheader("2. 詳細功能規格 (條列式)")
        
        # 預設填入您剛剛提供的優質內容
        frontend_default = """1. 專案引導：書名腦力激盪、視覺化目錄地圖 (Visual TOC Map)。
2. 積木式內容生成：模組化積木設計、寫作風格模擬器。
3. 雙語查核：實時雙語對照視圖、參考資料驗證 (RAG)。"""

        backend_default = """1. 格式封裝引擎：EPUB3 封裝、自動雙語 CSS 排版、TTS 語音檔生成與 Media Overlays 嵌入。
2. AI 管線：串接 LLM 進行翻譯與風格模擬。
3. 用戶管理：多作者協作、版本控制。"""

        db_default = """1. PostgreSQL：儲存使用者、書籍專案、章節結構。
2. 結構化文本 (Structured Text)：紀錄 Block 原文、譯文、語音路徑。"""

        frontend_req = st.text_area("💻 前端功能 (Frontend)", value=frontend_default, height=150)
        backend_req = st.text_area("⚙️ 後端功能 (Backend)", value=backend_default, height=150)
        db_req = st.text_area("🗄️ 資料庫需求 (Database)", value=db_default, height=100)

        submitted = st.form_submit_button("🚀 組合需求並生成藍圖", type="primary")

    # --- 送出後的處理邏輯 ---
    if submitted:
        # 1. 組合 Prompt (把分散的積木組起來)
        full_prompt = f"""
        專案名稱：{project_name}
        專案描述：{project_desc}
        
        【前端需求】：
        {frontend_req}
        
        【後端需求】：
        {backend_req}
        
        【資料庫需求】：
        {db_req}
        """
        
        with st.spinner("🤖 正在經由 HTTP 通道連線 AI 大腦... (這會繞過版本錯誤)"):
            # 呼叫新的 engine
            result_files = engine.generate_blueprint(full_prompt)
            
            if "error" in result_files:
                st.error(result_files["error"])
            else:
                st.success(f"🎉 生成成功！(使用模型: {result_files.get('_model_used')})")
                
                # 建立四個頁籤
                tab1, tab2, tab3, tab4 = st.tabs(["📘 README", "⚙️ SPEC", "📊 REPORT", "✅ TODO"])
                
                # Helper function for display and download
                def show_tab(tab, filename):
                    with tab:
                        content = result_files.get(filename, "無內容")
                        st.markdown(content)
                        st.download_button(f"下載 {filename}", content, filename)

                show_tab(tab1, "README.md")
                show_tab(tab2, "SPEC.md")
                show_tab(tab3, "REPORT.md")
                show_tab(tab4, "TODOLIST.md")
