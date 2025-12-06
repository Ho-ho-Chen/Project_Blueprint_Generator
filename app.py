import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 CSS 優化
# ==========================================
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stHorizontalBlock"] { align-items: center; }
    
    /* 調整頂部內容的邊距 */
    .block-container {
        /* ⚠️ 關鍵修正：將 1rem 改為 6rem，確保標題有足夠空間顯示 */
        padding-top: 6rem !important; 
        padding-bottom: 5rem !important;
    }
    
    /* 讓側邊欄按鈕填滿寬度 */
    .stButton button {
        width: 100%;
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

    # ==========================================
    # 👇 側邊欄：功能中控台
    # ==========================================
    with st.sidebar:
        # 👇 修改點 1：更換歡迎語
        st.success("歡迎光臨，軟體架構師") 
        st.info("💡 模式：HTTP 直連 (雙語版)") 
        
        st.markdown("---")
        st.markdown("### 🛠️ 專案控制台")
        
        # Button 1: 生成藍圖
        is_disabled_1 = (st.session_state.workflow_stage != 1)
        help_msg = "請先在右側填寫問卷" if st.session_state.workflow_stage == 0 else "點擊生成規格書"
        st.button("1. 生成藍圖 (Step 1)", disabled=is_disabled_1, key="btn_step1", help=help_msg, on_click=on_click_blueprint)
        
        # Button 2: 生成架構
        is_disabled_2 = (st.session_state.workflow_stage != 2)
        st.button("2. 生成架構 (Step 2)", disabled=is_disabled_2, key="btn_step2", on_click=on_click_structure)
        
        # Button 3: 下載文件
        if st.session_state.workflow_stage == 2 and st.session_state.result_files:
            zip_data = engine.create_zip_download(st.session_state.result_files)
            st.download_button("3. 下載完整文件包 (.zip)", data=zip_data, file_name="project.zip", mime="application/zip")
        else:
            st.button("3. 下載完整文件包 (.zip)", disabled=True, key="btn_dl_fake")

        # Button 4: 新專案
        st.markdown("---")
        st.button("🔄 開啟新專案", type="primary", on_click=on_click_reset)
        
        # 登出放在最下面
        st.markdown("---")
        if st.button("🔒 登出系統"):
            st.session_state.logged_in = False
            st.rerun()

    # ==========================================
    # 👇 主畫面 (Main Content)
    # ==========================================
    
    st.markdown('## 🏗️ PolyGlot 架構師')
    st.caption("從點子到藍圖，只要一瞬間")
    
    st.markdown("---") 

    # ----------------------------------------------------
    # 🔄 智慧引導流程 (Main Workflow)
    # ----------------------------------------------------

    # === Stage 0: 構想輸入 ===
    if st.session_state.workflow_stage == 0:
        st.info("👋 歡迎！請在下方告訴我您的初步構想，我會協助您釐清規格。")
        
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
        st.info("AI 發現了一些細節需要確認，請回答以下問題，然後點擊左側的 **「1. 生成藍圖」**。")
        
        q_data = st.session_state.questions
        
        c_q1, c_q2, c_q3 = st.columns(3)
        with c_q1:
            st.markdown(f"**🔹 前端/介面：**\n{q_data.get('q_frontend', '無問題')}")
            st.text_area("您的回答 (Frontend)", key="ans_fe", height=150)
        with c_q2:
            st.markdown(f"**🔹 後端/邏輯：**\n{q_data.get('q_backend', '無問題')}")
            st.text_area("您的回答 (Backend)", key="ans_be", height=150)
        with c_q3:
            st.markdown(f"**🔹 資料/儲存：**\n{q_data.get('q_database', '無問題')}")
            st.text_area("您的回答 (Database)", key="ans_db", height=150)
            
        # 觸發邏輯
        if st.session_state.trigger_blueprint:
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
            
            # 👇 使用 container(height=...) 鎖定高度
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("#### 📁 檔案結構")
                with st.container(height=500):
                    st.code(s_data.get("STRUCTURE.txt", "無內容"), language="text")
            
            with c2:
                # 👇 改名為「功能流程圖」
                st.markdown("#### 🔄 功能流程圖")
                with st.container(height=500):
                    mermaid = s_data.get("FLOW.mermaid", "")
                    if mermaid:
                        st.markdown(f"```mermaid\n{mermaid}\n```")
                    else:
                        st.warning("流程圖生成失敗")
