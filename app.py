import streamlit as st
import google.generativeai as genai
import config
import auth
import generator_engine as engine

# ==========================================
# 🚑 系統健康檢查區 (System Health Check)
# 用途：確認雲端環境是否已安裝正確的 Google AI 套件版本
# ==========================================
try:
    current_version = genai.__version__
    st.write(f"🔍 系統偵測：Google AI SDK 版本為 **{current_version}**")
    
    # 我們需要 0.8.3 以上才能支援 Gemini 1.5/2.0
    if current_version < "0.8.3":
        st.error(f"""
        ❌ **版本過舊 (Critical Error)**
        
        目前版本：{current_version}
        需求版本：>= 0.8.3
        
        **修復教學：**
        1. 請回到 GitHub 確認 `requirements.txt` 檔案名稱全小寫且拼字正確。
        2. 確認內容包含 `google-generativeai>=0.8.3`。
        3. 如果都正確，請在 Streamlit 後台 **刪除此 App (Delete)** 並 **重新部署 (New App)** 以強制更新快取。
        """)
        st.stop() # 停止執行下方程式，避免報錯
    else:
        st.success("✅ **環境檢測通過！** Google AI 套件版本符合需求，可正常連線。")
        
except Exception as e:
    st.error(f"❌ 無法偵測版本，環境嚴重異常：{e}")
    st.stop()
# ==========================================


# --- 1. 初始化頁面設定 ---
config.setup_page()

# --- 2. 獲取機密資料 (Key 和 Password) ---
api_key, app_password = config.get_credentials()

# --- 3. 初始化登入狀態 ---
auth.init_session_state()

# --- 4. 主流程控制 ---
if not auth.is_logged_in():
    # [情境 A]：未登入
    auth.login_page(app_password)
    
else:
    # [情境 B]：已登入 (顯示主程式)
    
    # 初始化 AI 引擎
    engine.configure_genai(api_key)
    
    # --- 側邊欄 ---
    with st.sidebar:
        st.success("✅ 歡迎回來，老師！")
        st.info("🔑 API Key 已自動載入")
        
        st.markdown("---")
        # 顯示使用的模型資訊 (這裡可以不用顯示版本了，上方已有檢查)
        st.caption("AI Engine: Google Gemini")
        
        st.markdown("---")
        auth.logout_button() # 登出按鈕

    # --- 主畫面 ---
    st.title("🏗️ AI 軟體架構師")
    st.markdown("#### 從點子到藍圖，生成全套工程文件")
    
    st.info("💡 輸入點子後，系統將自動產出：README, SPEC, Report, TodoList 四份標準文件。")

    product_idea = st.text_area(
        "你的產品點子是什麼？", 
        placeholder="例如：我想做一個專門給素食者的食譜分享 App，要有地圖功能、不含蛋奶的篩選器...",
        height=150
    )

    # --- 生成按鈕邏輯 ---
    if st.button("🚀 生成全套專案文件", type="primary"):
        if not product_idea:
            st.warning("請先輸入您的產品點子！")
        else:
            with st.spinner("🤖 架構師正在思考中... (若超過 30 秒請稍候，正在嘗試最佳模型)"):
                
                # 呼叫 engine 獲取字典格式的結果
                result_files = engine.generate_blueprint(product_idea)
                
                # 錯誤處理
                if "error" in result_files:
                    st.error(result_files["error"])
                else:
                    # 顯示成功訊息與使用的模型
                    used_model = result_files.get("_model_used", "Unknown")
                    st.success(f"🎉 文件生成完畢！(使用模型: {used_model})")
                    
                    # 建立四個頁籤
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📘 README.md", 
                        "⚙️ SPEC.md", 
                        "📊 REPORT.md", 
                        "✅ TODOLIST.md"
                    ])
                    
                    # 定義一個 helper function 來顯示並提供下載
                    def show_tab_content(tab, filename):
                        with tab:
                            content = result_files.get(filename, "無內容")
                            st.markdown(content)
                            st.download_button(
                                label=f"下載 {filename}",
                                data=content,
                                file_name=filename,
                                mime="text/markdown"
                            )

                    # 填入各頁籤內容
                    show_tab_content(tab1, "README.md")
                    show_tab_content(tab2, "SPEC.md")
                    show_tab_content(tab3, "REPORT.md")
                    show_tab_content(tab4, "TODOLIST.md")
