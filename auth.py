import streamlit as st

def init_session_state():
    """初始化登入狀態"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def login_page(correct_password):
    """
    顯示登入介面
    Args:
        correct_password: 從 config 傳入的正確密碼
    """
    st.markdown("## 🔒 系統鎖定中")
    st.markdown("請輸入授權密碼以存取 **AI 軟體架構師** 工具。")

    # 定義驗證回調函數
    def _check():
        if st.session_state.password_input == correct_password:
            st.session_state.logged_in = True
            del st.session_state.password_input # 清除輸入框
        else:
            st.error("❌ 密碼錯誤，請重新輸入。")

    st.text_input(
        "訪問密碼：", 
        type="password", 
        key="password_input", 
        on_change=_check
    )
    st.markdown("---")
    st.caption("© 2025 AI 軟體架構師 | 僅限授權人員使用")

def logout_button():
    """側邊欄的登出按鈕"""
    if st.sidebar.button("🚪 登出系統"):
        st.session_state.logged_in = False
        st.rerun()

def is_logged_in():
    """回傳目前是否登入"""
    return st.session_state.get('logged_in', False)
