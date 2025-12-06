import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 CSS 魔法：
#    1. 隱藏預設選單
#    2. 設定「吸頂標題列」樣式
# ==========================================
st.markdown("""
    <style>
    /* 隱藏 Streamlit 原生選單與按鈕 */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 調整頂部內容的邊距，讓它貼齊最上方 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }

    /* 關鍵 CSS：鎖定標題列 (Sticky Header)
       這會選取 App 的第一個容器 (包含標題和按鈕的那一塊)
       並將其設為 sticky (黏性)，滑動時會固定在頂部
    */
    div[data-testid="stVerticalBlock"] > div:first-child {
        position: sticky;
        top: 0;
        z-index: 999;       /* 確保在最上層 */
        background-color: #0e1117; /* 與背景同色，避免透明 */
        padding-top: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #333; /* 底部加一條線區隔 */
        margin-bottom: 20px;
    }
    
    /* 微調按鈕垂直對齊 */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 👇 簡易登入系統
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.workflow_stage = 0 

def check_login():
    user_pass = st.session_state.get("password_input", "")
    secret_pass = st.secrets.get("APP_PASSWORD", "12345678")
    if user_pass == secret_pass:
        st.session_state.logged_in = True
        st.session_state.password_input = "" 
    else:
        st.error("❌ 密碼錯誤")

if not st.session_state.logged_in:
    st.markdown("## 🔒 系統鎖定中")
    st.info("請輸入授權密碼以進入系統。")
    st.text_input("密碼：", type="password", key="password_input", on_change=check_login)

else:
    # 🔓 解鎖後的主程式
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    engine.configure_genai(api_key)

    # 側邊欄
    with st.sidebar:
        st.success("✅ 驗證通過")
        st.info("💡 模式：HTTP 直連 (雙語版)") 
        st.markdown("---")
        if st.button("🔒 登出系統"):
            st.session_state.logged_in = False
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ==========================================
    # 👇 頂部中控台 (Header Control Panel)
    # ==========================================
    
    # 【版面配置調整】
    # 使用 [2.5, 5, 2.5] 的比例
    # 左邊 (2.5): 標題
    # 中間 (5.0): 按鈕區 (縮短寬度，不要佔滿全螢幕)
    # 右邊 (2.5): 空白緩衝區 (用來把按鈕往左擠，使其緊湊)
    c_title, c_btns, c_empty = st.columns([2.5, 5, 2.5])
    
    with c_title:
        # 使用 markdown 取代 title 以減少預設留白，讓高度更緊湊
        st.markdown("### 🏗️ PolyGlot 架構師")
        
    with c_btns:
        # 在中間的 5.0 區域內，再切分 4 個等寬按鈕
        b1, b2, b3, b4 = st.columns(4)
        
        # Button 1: 生成藍圖
        with b1:
            is_disabled_1 = (st.session_state.workflow_stage != 1)
            help_msg = "請先填寫下方構想並開始諮詢" if st.session_state.workflow_stage == 0 else "點擊生成規格書"
            if st.button("1.生成藍圖", disabled=is_disabled_1, key="btn_step1", help=help_msg):
                st.session_state.trigger_blueprint = True
        
        # Button 2: 生成架構
        with b2:
            is_disabled_2 = (st.session_state.workflow_stage != 2)
            if st.button("2.生成架構", disabled=is_disabled_2, key="btn_step2"):
                st.session_state.trigger_structure = True
        
        # Button 3: 下載
        with b3:
            if st.session_state.workflow_stage == 2 and "result_files" in st.session_state:
                zip_data = engine.create_zip_download(st.session_state.result_files)
                st.download_button("3.下載文件", data=zip_data, file_name="project.zip", mime="application/zip")
            else:
                st.button("3.下載文件", disabled=True, key="btn_dl_fake")

        # Button 4: 新專案
        with b4:
            if st.button("4.新專案", type="primary"):
                st.session_state.workflow_stage = 0
                keys_to_reset = ["questions", "result_files", "structure_res", "project_name", "project_desc", "ans_fe", "ans_be", "ans_db"]
                for k in keys_to_reset:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    # 右邊 c_empty 留白，不做任何事，這樣按鈕就不會拉長到最右邊
    
    # ----------------------------------------------------
    # 🔄 智慧引導流程 (Main Workflow)
    # ----------------------------------------------------

    # === Stage 0: 構想輸入 ===
    if st.session_state.workflow_stage == 0:
        st.info("👋 歡迎！我是您的 AI 架構顧問。請告訴我您的初步想法，我會協助您釐清規格。")
        
        with st.form("stage0_form"):
            c1, c2 = st.columns([1, 2])
            p_name = c1.text_input("專案名稱", value="PolyGlotBook AI")
            p_desc = c2.text_area("我想做什麼？", height=100, 
                                  value="我想做一個網站，可以自動把文章變成中英對照的電子書，還要有語音朗讀功能。")
            
            if st.form_submit_button("🤖 開始諮詢 (AI 分析需求)"):
                with st.spinner("正在分析您的點子並設計問卷..."):
                    questions = engine.generate_interview_questions(p_name, p_desc)
                    if "error" in questions:
                        st.error(questions["error"])
                    else:
                        st.session_state.project_name = p_name
                        st.session_state.project_desc = p_desc
                        st.session_state.questions = questions
                        st.session_state.workflow_stage = 1
                        st.rerun()

    # === Stage 1: AI 訪談問卷 ===
    elif st.session_state.workflow_stage == 1:
        st.success(f"✅ 已分析專案：{st.session_state.get('project_name')}")
        st.markdown("### 📋 需求釐清問卷")
        st.caption("AI 發現了一些細節需要確認，請回答以下問題：")
        
        q_data = st.session_state.questions
        
        c_q1, c_q2, c_q3 = st.columns(3)
        with c_q1:
            st.info(f"**前端/介面：**\n{q_data.get('q_frontend', '無問題')}")
            st.text_area("您的回答 (Frontend)", key="ans_fe", height=150)
        with c_q2:
            st.info(f"**後端/邏輯：**\n{q_data.get('q_backend', '無問題')}")
            st.text_area("您的回答 (Backend)", key="ans_be", height=150)
        with c_q3:
            st.info(f"**資料/儲存：**\n{q_data.get('q_database', '無問題')}")
            st.text_area("您的回答 (Database)", key="ans_db", height=150)
            
        st.warning("👉 請填寫完畢後，點擊上方頂部的 **「1.生成藍圖」** 按鈕。")

        # 處理頂部按鈕觸發
        if st.session_state.get("trigger_blueprint"):
            ans_fe = st.session_state.get("ans_fe", "")
            ans_be = st.session_state.get("ans_be", "")
            ans_db = st.session_state.get("ans_db", "")
