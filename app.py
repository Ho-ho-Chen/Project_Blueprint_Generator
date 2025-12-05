import streamlit as st
import config
import auth
import generator_engine as engine

# --- 1. 初始化與登入檢查 ---
config.setup_page()
api_key, app_password = config.get_credentials()
auth.init_session_state()

if not auth.is_logged_in():
    auth.login_page(app_password)
else:
    # 傳遞 API Key 給引擎 (但不進行 SDK 設定，因為我們改用 REST API)
    engine.configure_genai(api_key)
    
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("💡 模式：REST API 直連 (已繞過舊版限制)")
        st.markdown("---")
        auth.logout_button()

    st.title("🏗️ PolyGlot 架構生成器")
    st.markdown("#### 分段輸入您的構想，生成標準化開發文件")
    
    # --- 改為分段式輸入表單 ---
    with st.form("project_input_form"):
        st.subheader("1. 專案基本資訊")
        col1, col2 = st.columns([1, 3])
        project_name = col1.text_input("專案名稱", value="PolyGlotBook AI")
        project_desc = col2.text_input("一句話描述", value="一站式生成雙語對照、有聲朗讀 EPUB3 的 SaaS 平台")

        st.markdown("---")
        st.subheader("2. 詳細功能規格")
        
        # 使用 expander 讓畫面整潔，預設展開
        frontend_req = st.text_area(
            "💻 前端功能 (Frontend)",
            height=150,
            value="1. 專案引導：書名腦力激盪、視覺化目錄地圖 (Visual TOC Map)。\n2. 積木式內容生成：模組化積木設計、寫作風格模擬器。\n3. 雙語查核：實時雙語對照視圖、參考資料驗證 (RAG)。"
        )
        
        backend_req = st.text_area(
            "⚙️ 後端功能 (Backend)",
            height=150,
            value="1. 格式封裝引擎：EPUB3 封裝、自動雙語 CSS 排版、TTS 語音檔生成與 Media Overlays 嵌入。\n2. AI 管線：串接 LLM 進行翻譯與風格模擬。\n3. 用戶管理：多作者協作、版本控制。"
        )
        
        db_req = st.text_area(
            "🗄️ 資料庫需求 (Database)",
            height=100,
            value="1. PostgreSQL：儲存使用者、書籍專案、章節結構。\n2. 結構化文本 (Structured Text)：紀錄 Block 原文、譯文、語音路徑。"
        )

        submitted = st.form_submit_button("🚀 組合需求並生成藍圖", type="primary")

    # --- 送出後的處理邏輯 ---
    if submitted:
        if not frontend_req or not backend_req:
            st.warning("請至少填寫前端與後端功能！")
        else:
            # 1. 組合 Prompt
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
                    
                    # 顯示頁籤
                    tabs = st.tabs(["📘 README", "⚙️ SPEC", "📊 REPORT", "✅ TODO"])
                    files_map = ["README.md", "SPEC.md", "REPORT.md", "TODOLIST.md"]
                    
                    for i, tab in enumerate(tabs):
                        filename = files_map[i]
                        with tab:
                            content = result_files.get(filename, "無內容")
                            st.markdown(content)
                            st.download_button(f"下載 {filename}", content, filename)
