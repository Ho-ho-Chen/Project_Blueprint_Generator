import streamlit as st
import config
import auth
import generator_engine as engine

config.setup_page()
api_key, app_password = config.get_credentials()
auth.init_session_state()

if not auth.is_logged_in():
    auth.login_page(app_password)
else:
    engine.configure_genai(api_key)
    
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("💡 連線模式：HTTP 直連 (強製版)") # 我改了這裡的字，讓您可以確認是否更新成功
        st.markdown("---")
        auth.logout_button()

    st.title("🏗️ PolyGlot 架構生成器")

    with st.form("project_input_form"):
        st.subheader("1. 專案基本資訊")
        col1, col2 = st.columns([1, 2])
        project_name = col1.text_input("專案名稱", value="PolyGlotBook AI")
        project_desc = col2.text_input("描述", value="一站式生成雙語對照 EPUB3")

        st.markdown("---")
        st.subheader("2. 詳細規格")
        frontend_req = st.text_area("💻 前端需求", height=100, value="書名腦力激盪、視覺化目錄、積木式編輯、雙語對照視圖")
        backend_req = st.text_area("⚙️ 後端需求", height=100, value="EPUB3 封裝引擎、TTS 語音生成、AI 翻譯管線")
        db_req = st.text_area("🗄️ 資料庫需求", height=80, value="PostgreSQL、結構化文本 (Structured Text)")

        submitted = st.form_submit_button("🚀 生成藍圖")

    if submitted:
        full_prompt = f"專案：{project_name}\n前端：{frontend_req}\n後端：{backend_req}\n資料庫：{db_req}"
        
        with st.spinner("🤖 正在強力連線中 (HTTP)..."):
            result_files = engine.generate_blueprint(full_prompt)
            
            if "error" in result_files:
                st.error(result_files["error"])
            else:
                st.success("🎉 生成成功！")
                tab1, tab2, tab3, tab4 = st.tabs(["README", "SPEC", "REPORT", "TODO"])
                
                # 簡化顯示邏輯
                files = ["README.md", "SPEC.md", "REPORT.md", "TODOLIST.md"]
                tabs = [tab1, tab2, tab3, tab4]
                
                for i, filename in enumerate(files):
                    with tabs[i]:
                        st.markdown(result_files.get(filename, ""))
