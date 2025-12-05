import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 優化 1：視覺隱藏 Manage App 按鈕與選單
#    這能讓一般使用者看不到右下角的 "Manage App"
#    以及右上角的開發者選單，讓介面更像一個獨立 App
# ==========================================
st.markdown("""
    <style>
    /* 隱藏右下角的 Manage App 按鈕 */
    .stDeployButton {display:none;}
    
    /* 隱藏右上角的三點選單 (Deploy, Settings 等) */
    #MainMenu {visibility: hidden;}
    
    /* 隱藏底部的 Streamlit 浮水印 */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 👇 原有邏輯：簡易密碼鎖 (The Lock)
# ==========================================

# 1. 初始化登入狀態
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    """驗證密碼函式"""
    user_pass = st.session_state.get("password_input", "")
    # 嘗試讀取 APP_PASSWORD (新建議)，如果沒有則讀取舊的 app_password，再沒有則預設
    secret_pass = st.secrets.get("APP_PASSWORD", st.secrets.get("app_password", "12345678"))
    
    if user_pass == secret_pass:
        st.session_state.logged_in = True
        st.session_state.password_input = "" # 清除輸入框
    else:
        st.error("❌ 密碼錯誤，請重新輸入")

# 2. 判斷是否鎖定
if not st.session_state.logged_in:
    # 🔒 [鎖定狀態]
    st.markdown("## 🔒 系統鎖定中")
    st.info("為了保護 API 資源與設定，請輸入授權密碼以繼續。")
    
    st.text_input(
        "請輸入密碼：", 
        type="password", 
        key="password_input", 
        on_change=check_login
    )
    st.caption("Hint: 請確認 Secrets 中已設定 APP_PASSWORD")

else:
    # 🔓 [解鎖狀態]：以下為您原本的完整程式碼
    
    # 取得 API Key
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    
    # 傳遞 Key 給引擎
    engine.configure_genai(api_key)
    
    with st.sidebar:
        st.success("✅ 驗證通過，歡迎老師！")
        st.info("💡 連線模式：HTTP 直連 (雙語版)") 
        st.markdown("---")
        
        # 自製的登出按鈕
        if st.button("🔒 登出系統"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🏗️ PolyGlot 架構生成器")

    # --- Step 1: 專案需求輸入表單 ---
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

        submitted = st.form_submit_button("🚀 生成藍圖 (Step 1)")

    # --- 處理 Step 1 生成邏輯 ---
    if submitted:
        full_prompt = f"專案：{project_name}\n前端：{frontend_req}\n後端：{backend_req}\n資料庫：{db_req}"
        
        with st.spinner("🤖 正在強力連線中 (HTTP)..."):
            result_files = engine.generate_blueprint(full_prompt)
            
            if "error" in result_files:
                st.error(result_files["error"])
            else:
                st.session_state.result_files = result_files
                st.session_state.step1_done = True
                
                # 👇 優化：若重新生成 Step 1，則重置 Step 2 狀態，避免資料不一致
                if "step2_done" in st.session_state:
                    del st.session_state.step2_done
                    del st.session_state.structure_res
                
                st.success("🎉 文件生成成功！")

    # --- 顯示 Step 1 結果 & 新增功能入口 ---
    if st.session_state.get("step1_done"):
        result_files = st.session_state.result_files
        
        st.markdown("---")
        st.subheader("📄 專案文件預覽")
        
        # 1. 頁籤顯示文件
        tab1, tab2, tab3, tab4 = st.tabs(["README", "SPEC", "REPORT", "TODO"])
        files_map = ["README.md", "SPEC.md", "REPORT.md", "TODOLIST.md"]
        
        for i, filename in enumerate(files_map):
            with [tab1, tab2, tab3, tab4][i]:
                st.markdown(result_files.get(filename, ""))

        # 2. 【新功能】下載與 Step 2 按鈕區
        st.markdown("### 📥 導出與進階生成")
        col_dl, col_step2 = st.columns([1, 2])
        
        with col_dl:
            # 呼叫 engine 新增的打包功能
            zip_data = engine.create_zip_download(result_files)
            st.download_button(
                label="📦 下載完整文件包 (.zip)",
                data=zip_data,
                file_name=f"{project_name}_docs.zip",
                mime="application/zip",
                type="primary"
            )

        with col_step2:
            # 👇 優化：按鈕邏輯判斷 (避免按鈕一直重複出現)
            # 狀態 A: Step 2 還沒做 -> 顯示「生成」按鈕
            if not st.session_state.get("step2_done"):
                if st.button("🏗️ Step 2: 生成檔案架構與流程圖"):
                    with st.spinner("正在根據規格書繪製架構圖..."):
                        context = result_files.get("README.md", "") + "\n" + result_files.get("SPEC.md", "")
                        structure_res = engine.generate_structure(context)
                        
                        if "STRUCTURE.txt" in structure_res:
                            st.session_state.structure_res = structure_res
                            st.session_state.step2_done = True
                            st.rerun() # 重新整理頁面，讓按鈕消失，直接顯示下方結果
                        else:
                            st.error("架構生成失敗，請重試")
            
            # 狀態 B: Step 2 做完了 -> 顯示「重新生成」按鈕
            else:
                if st.button("🔄 重新生成架構"):
                    st.session_state.step2_done = False
                    st.rerun()

    # --- 顯示 Step 2 結果 (視覺化) ---
    if st.session_state.get("step2_done") and "structure_res" in st.session_state:
        st.markdown("---")
        st.subheader("📊 架構可視化與流程閉環")
        
        struct_data = st.session_state.structure_res
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 📁 專案檔案結構")
            # 顯示檔案樹
            st.code(struct_data.get("STRUCTURE.txt", "無內容"), language="text")
            st.caption("建議依照此結構建立資料夾")

        with c2:
            st.markdown("#### 🔄 核心功能運作流程")
            mermaid_code = struct_data.get("FLOW.mermaid", "")
            if mermaid_code:
                # 使用 Streamlit 原生 Markdown 渲染 Mermaid
                st.markdown(f"""
                ```mermaid
                {mermaid_code}
                ```
                """)
                st.caption("此圖表展示了系統運作的時序邏輯")
            else:
                st.warning("流程圖生成失敗")
