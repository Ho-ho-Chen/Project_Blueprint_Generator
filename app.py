# ==========================================
# app.py: 架構產生器主程式
# ==========================================
import streamlit as st
import time
import datetime
from config import DEFAULT_BLUEPRINT
from generator_engine import call_ai_architect, create_project_zip

st.set_page_config(page_title="AI 架構師", page_icon="🏗️", layout="wide")

# 初始化
if 'blueprint' not in st.session_state:
    st.session_state['blueprint'] = DEFAULT_BLUEPRINT

# --- 側邊欄 ---
with st.sidebar:
    st.title("🏗️ AI 架構師")
    
    # API Key (優先讀 Secrets)
    api_key = None
    try:
        if st.secrets and "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ Key 已載入")
    except: pass
    
    if not api_key:
        api_key = st.text_input("🔑 API Key", type="password")

    st.divider()
    st.header("💡 您的點子 (Idea)")
    user_idea = st.text_area("你想做什麼？", "例如：一個幫忙自動記帳並分析消費習慣的 Line 機器人", height=150)
    
    if st.button("✨ 生成藍圖", type="primary", use_container_width=True):
        if not api_key:
            st.error("請輸入 API Key")
        else:
            with st.spinner("AI 架構師正在繪圖..."):
                data = call_ai_architect(user_idea, api_key)
                if data and "error" not in data:
                    st.session_state['blueprint'] = data
                    st.success("完成！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"失敗: {data.get('error', '未知錯誤')}")

    st.divider()
    
    # 下載區
    bp = st.session_state['blueprint']
    zip_buffer = create_project_zip(bp)
    st.download_button(
        label="📦 下載全套文件 (.zip)",
        data=zip_buffer,
        file_name=f"{bp.get('project_name', 'Project')}_Docs.zip",
        mime="application/zip"
    )

# --- 主畫面 ---
bp = st.session_state['blueprint']

st.header(f"📐 {bp.get('project_name', '新專案')}")

tab1, tab2, tab3, tab4 = st.tabs(["📄 README", "📐 SPEC", "✅ TODO", "📝 REPORT"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        bp['project_name'] = st.text_input("專案名稱", bp.get('project_name'))
        bp['description'] = st.text_area("專案描述", bp.get('description'), height=200)
    with c2:
        bp['values'] = st.text_area("核心價值", bp.get('values'), height=100)
        bp['tech_stack'] = st.text_area("技術棧", bp.get('tech_stack'), height=100)

with tab2:
    c1, c2 = st.columns(2)
    with c1: bp['structure_tree'] = st.text_area("檔案結構", bp.get('structure_tree'), height=300)
    with c2: bp['data_schema'] = st.text_area("資料結構", str(bp.get('data_schema')), height=300)

with tab3:
    bp['todo_phase1'] = st.text_area("Phase 1 任務", bp.get('todo_phase1'), height=200)
    bp['todo_phase2'] = st.text_area("Phase 2 任務", bp.get('todo_phase2'), height=200)

with tab4:
    bp['risk_log'] = st.text_area("風險與筆記", bp.get('risk_log'), height=300)
