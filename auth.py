# ==========================================
# auth.py: 企業級門禁系統 (v82.0)
# 功能：登入、註冊、密碼重置、加密存儲
# ==========================================
import streamlit as st
import json
import os
import hashlib
import time

# 使用者資料庫檔案
USER_DB_FILE = "users.json"

def hash_password(password):
    """密碼加密 (SHA-256)"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_users():
    """讀取使用者資料庫 (若無則建立預設 boss 帳號)"""
    if not os.path.exists(USER_DB_FILE):
        default_db = {
            "boss": {
                "password": hash_password("admin888"),
                "recovery": "admin" # 安全提問答案
            }
        }
        # 自動建立檔案
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
    if st.session_state.get("logged_in", False):
        return True
    return False

def logout():
    """登出邏輯"""
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.rerun()

def login_system():
    """渲染登入/註冊/忘記密碼介面"""
    
    # 載入資料庫
    if 'users_db' not in st.session_state:
        st.session_state['users_db'] = load_users()
    
    # 標題美化
    st.markdown(
        """
        <style>
        .login-title { text-align: center; font-size: 2.5rem; color: #2ecc71; font-weight: bold; }
        .login-subtitle { text-align: center; color: gray; margin-bottom: 30px; }
        </style>
        <div class='login-title'>🛡️ AI 出版工廠門禁</div>
        <div class='login-subtitle'>Enterprise Access Control</div>
        """, unsafe_allow_html=True
    )
    
    # 置中佈局
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        # 分頁切換
        tab1, tab2, tab3 = st.tabs(["🔐 登入", "📝 註冊新帳號", "❓ 忘記密碼"])
        
        # --- 1. 登入頁面 ---
        with tab1:
            with st.form("login_form"):
                user = st.text_input("帳號")
                pwd = st.text_input("密碼", type="password")
                submit = st.form_submit_button("登入", use_container_width=True)
                
                if submit:
                    db = st.session_state['users_db']
                    # 驗證
                    if user in db and db[user]['password'] == hash_password(pwd):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user
                        st.success(f"歡迎回來，{user}！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ 帳號或密碼錯誤")

        # --- 2. 註冊頁面 ---
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("設定新帳號")
                new_pwd = st.text_input("設定密碼", type="password")
                new_pwd2 = st.text_input("確認密碼", type="password")
                recovery_q = st.text_input("安全提問：您第一隻寵物的名字？(用於找回密碼)")
                signup_btn = st.form_submit_button("註冊", use_container_width=True)
                
                if signup_btn:
                    db = st.session_state['users_db']
                    if new_user in db:
                        st.warning("此帳號已被註冊")
                    elif new_pwd != new_pwd2:
                        st.error("兩次密碼不一致")
                    elif not new_user or not new_pwd or not recovery_q:
                        st.error("請填寫完整資料")
                    else:
                        # 建立新用戶
                        db[new_user] = {
                            "password": hash_password(new_pwd),
                            "recovery": recovery_q
                        }
                        save_users(db)
                        st.session_state['users_db'] = db
                        st.success("🎉 註冊成功！請切換到「登入」頁籤進行登入。")

        # --- 3. 忘記密碼 ---
        with tab3:
            with st.form("forgot_form"):
                f_user = st.text_input("您的帳號")
                f_ans = st.text_input("請回答安全提問 (寵物名字)")
                new_reset_pwd = st.text_input("設定新密碼", type="password")
                reset_btn = st.form_submit_button("重置密碼", use_container_width=True)
                
                if reset_btn:
                    db = st.session_state['users_db']
                    if f_user in db:
                        if db[f_user].get('recovery') == f_ans:
                            db[f_user]['password'] = hash_password(new_reset_pwd)
                            save_users(db)
                            st.session_state['users_db'] = db
                            st.success("✅ 密碼已重置！請重新登入。")
                        else:
                            st.error("安全提問答案錯誤")
                    else:
                        st.error("找不到此帳號")
