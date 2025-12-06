import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 CSS 優化 (修復標題被擋住的問題)
# ==========================================
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* 隱藏 Streamlit 原生 Header */
    
    div[data-testid="stHorizontalBlock"] { align-items: center; }
    
    /* 調整頂部內容的邊距，稍微加大一點 */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 👇 核心修復：狀態初始化 & 回呼函式 (Callbacks)
# ==========================================

# 1. 確保所有狀態變數都有初始值
keys_to_init = [
    "logged_in", "workflow_stage", 
    "trigger_blueprint", "trigger_structure", 
    "project_name", "project_desc",
    "questions", "result_files", "structure_res",
    "ans_fe", "ans_be", "ans_db"
]
for key in keys_to_init:
    if key not in st.session_state:
        if key == "logged_in": st.session_state[key] = False
        elif key == "workflow_stage": st.session_state[key] = 0
        else: st.session_state[key] = None # 其他設為 None 或 False

# 2. 定義按鈕的回呼函式 (Click Handlers)
def on_click_blueprint():
    st.session_state.trigger_blueprint = True

def on_click_structure():
    st.session_state.trigger_structure = True

def on_click_reset():
    st.session_state.workflow_stage = 0
    # 清空相關資料
    for k in ["questions", "result_files", "structure_res", "ans_fe", "ans_be", "ans_db"]:
        st.session_state[k] = None

# ==========================================
# 👇 簡易登入系統
# ==========================================
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
            st.rerun()

    # ==========================================
    # 👇 關鍵修復：加入頂部隱形墊片 (Spacer)
    #    這會強制將內容往下推，確保標題不會被切掉
    # ==========================================
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

    # ==========================================
    # 👇 頂部中控台 (使用 Callback 綁定)
    # ==========================================
    
    c_title, c_btns, c_empty = st.columns([2.5, 5, 2.5])
    
    with c_title:
        # 使用 HTML h2 標籤確保樣式一致且不被遮擋
        st.markdown('<h3 style="margin:0; padding:0;">🏗️ PolyGlot 架構師</h3>', unsafe_allow_html=True)
        
    with c_btns:
        b1, b2, b3, b4 = st.columns(4)
        
        # Button 1: 生成藍圖
        with b1:
            is_disabled_1 = (st.session_state.workflow_stage != 1)
            help_msg = "請先填寫下方問卷" if st.session_state.workflow_stage == 0 else "點擊生成規格書"
            st.button("1.生成藍圖", disabled=is_disabled_1, key="btn_step1", help=help_msg, on_click=on_click_blueprint)
        
        # Button 2: 生成架構
        with b2:
            is_disabled_2 = (st.session_state.workflow_stage != 2)
            st.button("2.生成架構", disabled=is_disabled_2, key="btn_step2", on_click=on_click_structure)
        
        # Button 3: 下載
        with b3:
            if st.session_state.workflow_stage == 2 and st.session_state.result_files:
                zip_data = engine.create_zip_download(st.session_state.result_files)
                st.download_button("3.下載文件", data=zip_data, file_name="project.zip", mime="application/zip")
            else:
                st.button("3.下載文件", disabled=True, key="btn_dl_fake")

        # Button 4: 新專案
        with b4:
            st.button("4.新專案", type="primary", on_click=on_click_reset)

    st.markdown("---") 

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
        # 使用 key 綁定 session_state，確保輸入值不會丟失
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

        # 處理觸發邏輯 (現在由 on_click 驅動，非常穩定)
        if st.session_state.trigger_blueprint:
            # 再次確認輸入框有值
            ans_fe = st.session_state.get("ans_fe", "")
            ans_be = st.session_state.get("ans_be", "")
            ans_db = st.session_state.get("ans_db", "")
            
            full_req = f"""
            專案名稱：{st.session_state.project_name}
            原始構想：{st.session_state.project_desc}
            【訪談回答】：
            1. 前端：{ans_fe}
            2. 後端：{ans_be}
            3. 資料庫：{ans_db}
            """
            with st.spinner("AI 正在根據訪談結果撰寫規格書 (這可能需要 30 秒)..."):
                res = engine.generate_blueprint(full_req)
                if "error" in res:
                    st.error(res["error"])
                    # 如果失敗，重置按鈕狀態，讓使用者可以重試
                    st.session_state.trigger_blueprint = False
                else:
                    st.session_state.result_files = res
                    st.session_state.workflow_stage = 2
                    st.session_state.trigger_blueprint = False
                    st.rerun()

    # === Stage 2: 結果展示 ===
    elif st.session_state.workflow_stage == 2:
        res = st.session_state.result_files
        
        st.subheader("📄 規格藍圖預覽")
        t1, t2, t3, t4 = st.tabs(["README", "SPEC", "REPORT", "TODO"])
        with t1: st.markdown(res.get("README.md", ""))
        with t2: st.markdown(res.get("SPEC.md", ""))
        with t3: st.markdown(res.get("REPORT.md", ""))
        with t4: st.markdown(res.get("TODOLIST.md", ""))
        
        # 處理生成架構圖觸發
        if st.session_state.trigger_structure:
            with st.spinner("正在繪製架構圖..."):
                context = res.get("README.md", "") + "\n" + res.get("SPEC.md", "")
                struct_res = engine.generate_structure(context)
                st.session_state.structure_res = struct_res
                st.session_state.trigger_structure = False
                st.rerun()
        
        if st.session_state.get("structure_res"):
            st.markdown("---")
            st.subheader("📊 架構可視化")
            s_data = st.session_state.structure_res
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 📁 檔案結構")
                st.code(s_data.get("STRUCTURE.txt", "無內容"), language="text")
            with c2:
                st.markdown("#### 🔄 流程圖")
                mermaid = s_data.get("FLOW.mermaid", "")
                if mermaid:
                    st.markdown(f"```mermaid\n{mermaid}\n```")
                else:
                    st.warning("流程圖生成失敗")
