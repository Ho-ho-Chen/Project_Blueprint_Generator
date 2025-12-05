import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 CSS 優化：隱藏 Streamlit 原生選單 + 頂部凍結設定
# ==========================================
st.markdown("""
    <style>
    /* 1. 隱藏右下角的 Manage App 按鈕 & 右上角選單 */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. 定義頂部凍結區域的樣式 (Sticky Header) */
    /* 使用 sticky 可以讓它黏在頂部，但不會蓋住側邊欄 */
    div.block-container {
        padding-top: 0rem; /* 為了讓 Header 貼頂，減少預設留白 */
    }
    
    .sticky-header-container {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #0e1117; /* 深色背景，避免透明 */
        padding-top: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #333;
        margin-bottom: 20px;
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

    # ==========================================
    # 👇 關鍵修復：把側邊欄 (Sidebar) 加回來了！
    # ==========================================
    with st.sidebar:
        st.success("✅ 驗證通過，歡迎老師！")
        st.info("💡 連線模式：HTTP 直連 (雙語版)") 
        st.markdown("---")
        # 登出按鈕
        if st.button("🔒 登出系統"):
            st.session_state.logged_in = False
            # 清除所有狀態並重整
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ==========================================
    # 👇 頂部凍結中控台 (Sticky Control Panel)
    # ==========================================
    # 我們用一個 div 包起來，套用上面的 CSS class
    st.markdown('<div class="sticky-header-container">', unsafe_allow_html=True)
    
    c_title, c_btns = st.columns([1.5, 2.5])
    
    with c_title:
        st.title("🏗️ PolyGlot 架構師")
        
    with c_btns:
        # 放置四個功能按鈕
        b1, b2, b3, b4 = st.columns(4)
        
        # Button 1: 生成藍圖 (提交問卷)
        with b1:
            is_disabled_1 = (st.session_state.workflow_stage != 1)
            if st.button("1.生成藍圖", disabled=is_disabled_1, key="btn_step1", help="填寫完問卷後點擊"):
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
                keys_to_reset = ["questions", "result_files", "structure_res", "project_name", "project_desc"]
                for k in keys_to_reset:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) 
    # ☝️ 結束凍結區域

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
                    # 呼叫 engine
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
            ans_fe = st.text_area("您的回答 (Frontend)", key="ans_fe", height=150)
        with c_q2:
            st.info(f"**後端/邏輯：**\n{q_data.get('q_backend', '無問題')}")
            ans_be = st.text_area("您的回答 (Backend)", key="ans_be", height=150)
        with c_q3:
            st.info(f"**資料/儲存：**\n{q_data.get('q_database', '無問題')}")
            ans_db = st.text_area("您的回答 (Database)", key="ans_db", height=150)
            
        st.warning("👉 請填寫完畢後，點擊上方的 **「1.生成藍圖」** 按鈕。")

        # 處理頂部按鈕觸發
        if st.session_state.get("trigger_blueprint"):
            full_req = f"""
            專案名稱：{st.session_state.project_name}
            原始構想：{st.session_state.project_desc}
            【訪談回答】：
            1. 前端：{ans_fe}
            2. 後端：{ans_be}
            3. 資料庫：{ans_db}
            """
            with st.spinner("AI 正在根據訪談結果撰寫規格書..."):
                res = engine.generate_blueprint(full_req)
                if "error" in res:
                    st.error(res["error"])
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
        if st.session_state.get("trigger_structure"):
            with st.spinner("正在繪製架構圖..."):
                context = res.get("README.md", "") + "\n" + res.get("SPEC.md", "")
                struct_res = engine.generate_structure(context)
                st.session_state.structure_res = struct_res
                st.session_state.trigger_structure = False
                st.rerun()
        
        if "structure_res" in st.session_state:
            st.markdown("---")
            st.subheader("📊 架構可視化")
            s_data = st.session_state.structure_res
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 📁 檔案結構")
                st.code(s_data.get("STRUCTURE.txt", ""), language="text")
            with c2:
                st.markdown("#### 🔄 流程圖")
                mermaid = s_data.get("FLOW.mermaid", "")
                if mermaid:
                    st.markdown(f"```mermaid\n{mermaid}\n```")
