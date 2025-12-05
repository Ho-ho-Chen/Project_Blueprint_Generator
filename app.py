# ==========================================
# app.py: 前端介面 (Streamlit)
# ==========================================
import streamlit as st
import os
from generator_engine import call_ai_architect, create_project_zip

# 1. 設定頁面基礎資訊
st.set_page_config(
    page_title="AI 軟體架構生成器",
    page_icon="🏗️",
    layout="centered"
)

# 2. 側邊欄：設定 API Key
with st.sidebar:
    st.header("🔑 設定")
    api_key = st.text_input(
        "輸入 Google Gemini API Key", 
        type="password",
        help="請到 Google AI Studio 申請免費 Key"
    )
    st.markdown("---")
    st.markdown("### 關於本工具")
    st.info("這是一個 AI 輔助架構設計工具。輸入點子，自動生成規格書、資料結構與開發清單。")

# 3. 主畫面：標題與輸入區
st.title("🏗️ AI 軟體架構師")
st.markdown("### 從點子到藍圖，只要一瞬間")

# 使用者輸入點子
idea = st.text_area(
    "💡 你的產品點子是什麼？", 
    height=150,
    placeholder="例如：我想做一個專門給素食者的食譜分享 App，要有地圖功能..."
)

# 4. 執行邏輯
generate_btn = st.button("🚀 開始生成架構藍圖", type="primary")

if generate_btn:
    # 檢查是否都有填寫
    if not api_key:
        st.warning("⚠️ 請先在側邊欄輸入你的 Google API Key")
    elif not idea:
        st.warning("⚠️ 請輸入你的產品點子")
    else:
        # 顯示載入動畫
        with st.spinner("🤖 AI 架構師正在思考中... (約需 15-30 秒)"):
            # 呼叫後端引擎 (generator_engine.py)
            result = call_ai_architect(idea, api_key)

            # 錯誤處理
            if not result:
                st.error("❌ 未知錯誤，請檢查網路或 API Key。")
            elif "error" in result:
                st.error(f"❌ 發生錯誤：{result['error']}")
            else:
                # 成功！顯示結果
                st.success("✅ 架構生成完畢！")
                
                # 顯示專案名稱與簡介
                st.subheader(f"專案：{result.get('project_name', '未命名專案')}")
                st.write(result.get('description', ''))
                
                # 使用 Expander 收折詳細資訊，避免版面太亂
                with st.expander("查看技術棧 (Tech Stack)"):
                    st.write(result.get('tech_stack', ''))
                
                with st.expander("查看開發任務 (Todo List)"):
                    st.write("### Phase 1")
                    st.write(result.get('todo_phase1', ''))
                    st.write("### Phase 2")
                    st.write(result.get('todo_phase2', ''))

                # 產生 ZIP 檔案
                zip_buffer = create_project_zip(result)
                
                if zip_buffer:
                    # 下載按鈕
                    st.download_button(
                        label="📥 下載完整專案包 (ZIP)",
                        data=zip_buffer,
                        file_name=f"{result.get('project_name', 'project')}_blueprint.zip",
                        mime="application/zip"
                    )
                else:
                    st.error("打包 ZIP 失敗。")
