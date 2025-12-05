import streamlit as st

def setup_page():
    """設定網頁的基本資訊 (Title, Layout)"""
    st.set_page_config(
        page_title="AI 軟體架構師",
        page_icon="🏗️",
        layout="wide"
    )

def get_credentials():
    """
    安全地讀取 secrets
    回傳: (api_key, app_password) 的 Tuple
    """
    try:
        # 使用 .get 避免如果 key 不存在時直接報錯
        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        password = st.secrets.get("app_password", None)
        
        if not api_key or not password:
            st.error("⚠️ 設定檔錯誤：請確認 .streamlit/secrets.toml 已正確設定 API Key 與密碼。")
            st.stop()
            
        return api_key, password
    except FileNotFoundError:
        st.error("⚠️ 找不到 secrets.toml 檔案。請參考說明建立設定檔。")
        st.stop()
