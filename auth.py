# ==========================================
# auth.py: 企業級門禁系統 (v82.1 Security Fix)
# 功能：登入、註冊、密碼重置、加密存儲
# ==========================================
import streamlit as st
import json
import os
import hashlib
import time

# --- 設定區 ---
USER_DB_FILE = "users.json"
# [資安強化] 系統專用鹽值 (Salt)，請勿外流，這能讓駭客即便拿到資料庫也無法輕易還原密碼
SYSTEM_SALT = "s8#9kL!2_AI_PROJECT_SECRET_KEY_2025"

def make_hash(password):
    """
    [資安強化] 密碼加密 (SHA-256 + Salt)
    """
    salted_password = password + SYSTEM_SALT
    return hashlib.sha256(str.encode(salted_password)).hexdigest()

def load_users():
    """讀取使用者資料庫 (若無則建立預設 admin 帳號)"""
    if not os.path.exists(USER_DB_FILE):
        default_db = {
            "admin": {
                "password": make_hash("admin888"),
                "recovery": "admin_pet" # 預設安全提問答案
            }
        }
        save_users(default_db)
        return default_db
        
    try:
        with open(USER_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """儲存使用者資料庫"""
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def check_password():
    """
    檢查是否已登入
    回傳: True (已登入) / False (未登入)
    """
    return st.session_state.get("logged_in", False)

def logout_button():
    """在側邊欄顯示登出按鈕"""
    with st.sidebar:
        st.markdown(f"👤 目前使用者: **{st.session_state.get('user_id', 'Unknown')}**")
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.rerun()

def login_page():
    """渲染登入/註冊/忘記密碼介面 (阻擋未授權存取)"""
    
    # 初始化資料庫
    if 'users_db' not in st.session_state:
        st.session_state['users_db'] = load_users()
    
    # CSS 美化
    st.markdown(
        """
        <style>
        .login-title { text-align: center; font-size: 2rem; color: #2ecc71; font-weight: bold; margin-top: 20px;}
        .login-subtitle { text-align: center; color: gray; margin-bottom: 20px; }
        .stTabs [data-baseweb="tab-list"] { justify-content: center; }
        </style>
        <div class='login-title'>🛡️ 系統登入中心</div>
        <div class='login-subtitle'>Secure Access Control</div>
        """, unsafe_allow_html=True
    )
    
    # 置中佈局 (使用 columns 擠壓中間空間)
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        tab1, tab2, tab3 = st.tabs(["🔐 登入", "📝 註冊", "❓ 忘記密碼"])
        
        # --- 1. 登入 ---
        with tab1:
            with st.form("login_form"):
                user = st.text_input("帳號")
                pwd = st.text_input("密碼", type="password")
                submit = st.form_submit_button("登入", use_container_width=True)
                
                if submit:
                    db = st.session_state['users_db']
                    # [資安] 驗證雜湊值
                    if user in db and db[user]['password'] == make_hash(pwd):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user
                        st.success(f"歡迎回來，{user}！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ 帳號或密碼錯誤")

        # --- 2. 註冊 ---
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("新帳號 (User ID)")
                new_pwd = st.text_input("設定密碼", type="password")
                new_pwd2 = st.text_input("確認密碼", type="password")
                recovery_q = st.text_input("安全提問：您第一隻寵物的名字？")
                signup_btn = st.form_submit_button("註冊帳號", use_container_width=True)
                
                if signup_btn:
                    db = st.session_state['users_db']
                    if new_user in db:
                        st.warning("⚠️ 此帳號已被使用")
                    elif new_pwd != new_pwd2:
                        st.error("❌ 兩次密碼輸入不一致")
                    elif len(new_pwd) < 6:
                        st.error("❌ 為了安全，密碼長度需至少 6 碼")
                    elif not new_user or not recovery_q:
                        st.error("❌ 請填寫完整資料")
                    else:
                        # 建立新用戶 (存入加密後的密碼)
                        db[new_user] = {
                            "password": make_hash(new_pwd),
                            "recovery": recovery_q
                        }
                        save_users(db)
                        st.session_state['users_db'] = db
                        st.success("🎉 註冊成功！請切換至「登入」分頁。")

        # --- 3. 忘記密碼 ---
        with tab3:
            with st.form("forgot_form"):
                f_user = st.text_input("您的帳號")
                f_ans = st.text_input("安全提問答案 (寵物名字)")
                new_reset_pwd = st.text_input("設定新密碼", type="password")
                reset_btn = st.form_submit_button("重置密碼", use_container_width=True)
                
                if reset_btn:
                    db = st.session_state['users_db']
                    if f_user in db:
                        if db[f_user].get('recovery') == f_ans:
                            # 儲存新的加密密碼
                            db[f_user]['password'] = make_hash(new_reset_pwd)
                            save_users(db)
                            st.session_state['users_db'] = db
                            st.success("✅ 密碼已重置！請重新登入。")
                        else:
                            st.error("❌ 安全提問答案錯誤")
                    else:
                        st.error("❌ 找不到此帳號")
