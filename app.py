import streamlit as st
import config
import auth 
import generator_engine as engine

# --- 1. 初始化頁面 ---
config.setup_page()

# ==========================================
# 👇 CSS 魔法：建立「凍結置頂」的中控台
# ==========================================
st.markdown("""
    <style>
    /* 隱藏預設選單 */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 定義頂部凍結區域的樣式 */
    .sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 999;
        background-color: #0e1117; /* Streamlit 深色主題背景色 */
        padding: 10px 20px;
        border-bottom: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 為了不讓內容被頂部遮住，把主內容往下推 */
    .main .block-container {
        padding-top: 20px !important; /* 調整這個值來避免遮擋 */
    }
    
    /* 調整按鈕在頂部的排版 */
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
    # 初始化流程狀態：0=輸入構想, 1=填寫問卷, 2=生成結果
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
    
    # ----------------------------------------------------
    # 🏗️ 頂部凍結中控台 (Sticky Control Panel)
    # ----------------------------------------------------
    # 我們使用一個 container 來裝載標題和按鈕
    # 注意：Streamlit 原生無法完全 "Fixed"，但放在最上面是標準做法
    
    header_container = st.container()
    
    with header_container:
        col_title, col_btns = st.columns([1.5, 2.5])
        
        with col_title:
            st.title("🏗️ PolyGlot 架構師")
            
        with col_btns:
            # 這裡放置那四個關鍵按鈕，預設靠右排版 (利用 columns 空白推擠)
            # 依據目前的狀態 (workflow_stage) 決定按鈕是否可用
            
            b1, b2, b3, b4 = st.columns(4)
            
            # Button 1: 生成藍圖 (其實是提交問卷)
            with b1:
                # 只有在問卷階段 (1) 才能按
                is_disabled_1 = (st.session_state.workflow_stage != 1)
                if st.button("1.生成藍圖", disabled=is_disabled_1, help="填寫完問卷後點擊此處"):
                    st.session_state.trigger_blueprint = True
            
            # Button 2: 生成架構
            with b2:
                # 只有在結果階段 (2) 才能按
                is_disabled_2 = (st.session_state.workflow_stage != 2)
                if st.button("2.生成架構", disabled=is_disabled_2):
                    st.session_state.trigger_structure = True
            
            # Button 3: 下載
            with b3:
                if st.session_state.workflow_stage == 2 and "result_files" in st.session_state:
                    zip_data = engine.create_zip_download(st.session_state.result_files)
                    st.download_button("3.下載文件", data=zip_data, file_name="project.zip", mime="application/zip")
                else:
                    st.button("3.下載文件", disabled=True)

            # Button 4: 重置/重新開始
            with b4:
                if st.button("4.新專案", type="primary"):
                    # 重置所有狀態
                    st.session_state.workflow_stage = 0
                    if "questions" in st.session_state: del st.session_state.questions
                    if "result_files" in st.session_state: del st.session_state.result_files
                    if "structure_res" in st.session_state: del st.session_state.structure_res
                    st.rerun()

    st.markdown("---") # 分隔線

    # ----------------------------------------------------
    # 🔄 智慧引導流程 (Main Workflow)
    # ----------------------------------------------------

    # === Stage 0: 構想輸入 (新手模式) ===
    if st.session_state.workflow_stage == 0:
        st.info("👋 歡迎！我是您的 AI 架構顧問。請告訴我您的初步想法，我會協助您釐清規格。")
        
        with st.form("stage0_form"):
            c1, c2 = st.columns([1, 2])
            p_name = c1.text_input("專案名稱", value="PolyGlotBook AI")
            p_desc = c2.text_area("我想做什麼？(簡單描述即可)", height=100, 
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
                        st.session_state.workflow_stage = 1 # 進入下一階段
                        st.rerun()

    # === Stage 1: AI 訪談問卷 ===
    elif st.session_state.workflow_stage == 1:
        st.success(f"✅ 已分析專案：{st.session_state.project_name}")
        st.markdown("### 📋 需求釐清問卷")
        st.caption("AI 發現了一些細節需要確認，請回答以下問題（這會讓規格書更準確）：")
        
        q_data = st.session_state.questions
        
        # 這裡不使用 form，改用 session_state 綁定，配合頂部按鈕觸發
        col_q1, col_q2, col_q3 = st.columns(3)
        
        with col_q1:
            st.info(f"**前端/介面：**\n{q_data.get('q_frontend')}")
            ans_fe = st.text_area("您的回答 (Frontend)", key="ans_fe", height=150)
            
        with col_q2:
            st.info(f"**後端/邏輯：**\n{q_data.get('q_backend')}")
            ans_be = st.text_area("您的回答 (Backend)", key="ans_be", height=150)
            
        with col_q3:
            st.info(f"**資料/儲存：**\n{q_data.get('q_database')}")
            ans_db = st.text_area("您的回答 (Database)", key="ans_db", height=150)
            
        st.warning("👉 請填寫完畢後，點擊右上方頂部的 **「1.生成藍圖」** 按鈕。")

        # 處理頂部按鈕觸發的事件
        if st.session_state.get("trigger_blueprint"):
            # 組合完整的 Prompt
            full_req = f"""
            專案名稱：{st.session_state.project_name}
            原始構想：{st.session_state.project_desc}
            
            【詳細需求訪談】：
            1. 前端 ({q_data.get('q_frontend')})：{ans_fe}
            2. 後端 ({q_data.get('q_backend')})：{ans_be}
            3. 資料庫 ({q_data.get('q_database')})：{ans_db}
            """
            
            with st.spinner("AI 正在根據訪談結果撰寫規格書..."):
                res = engine.generate_blueprint(full_req)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.session_state.result_files = res
                    st.session_state.workflow_stage = 2 # 進入結果階段
                    st.session_state.trigger_blueprint = False # 重置觸發器
                    st.rerun()

    # === Stage 2: 結果展示與架構生成 ===
    elif st.session_state.workflow_stage == 2:
        res = st.session_state.result_files
        
        # 顯示四大文件
        st.subheader("📄 規格藍圖預覽")
        t1, t2, t3, t4 = st.tabs(["README", "SPEC", "REPORT", "TODO"])
        with t1: st.markdown(res.get("README.md", ""))
        with t2: st.markdown(res.get("SPEC.md", ""))
        with t3: st.markdown(res.get("REPORT.md", ""))
        with t4: st.markdown(res.get("TODOLIST.md", ""))
        
        # 處理「生成架構」按鈕觸發
        if st.session_state.get("trigger_structure"):
            with st.spinner("正在繪製架構圖..."):
                context = res.get("README.md", "") + "\n" + res.get("SPEC.md", "")
                struct_res = engine.generate_structure(context)
                st.session_state.structure_res = struct_res
                st.session_state.trigger_structure = False # 重置
        
        # 如果有架構圖結果，就顯示出來
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
