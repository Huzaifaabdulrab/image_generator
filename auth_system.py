import sqlite3
import streamlit as st
import hashlib

class AuthSystem:
    def __init__(self, db_path='users.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_users_table()
        self.hash_all_passwords_if_needed()
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
        if 'username' not in st.session_state:
            st.session_state['username'] = None

    def create_users_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                paid INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def hash_all_passwords_if_needed(self):
        self.cursor.execute("SELECT id, password FROM users")
        users = self.cursor.fetchall()
        updated = False
        for user_id, pw in users:
            # Agar password pehle se hashed (length 64 hex) nahi hai, hash kar do
            if len(pw) != 64:
                hashed_pw = self.hash_password(pw)
                self.cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
                updated = True
        if updated:
            self.conn.commit()

    def signup(self, username, password):
        username = username.strip()
        password = password.strip()
        hashed_pw = self.hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, username, password):
        username = username.strip()
        password = password.strip()
        hashed_pw = self.hash_password(password)
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
        user = self.cursor.fetchone()
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            return True
        return False

    def logout(self):
        for key in ['logged_in', 'username', 'checkout_url']:
            if key in st.session_state:
                del st.session_state[key]

    def mark_paid(self, username):
        self.cursor.execute("UPDATE users SET paid = 1 WHERE username = ?", (username,))
        self.conn.commit()

    def is_paid(self, username):
        self.cursor.execute("SELECT paid FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

# ---- Streamlit UI ----
auth = AuthSystem()

def main():
    st.title("User Authentication Demo")

    if st.session_state['logged_in']:
        st.success(f"Logged in as {st.session_state['username']}")
        st.header(f"Welcome to your Dashboard, {st.session_state['username']}!")

        if auth.is_paid(st.session_state['username']):
            st.info("You have premium access!")
        else:
            st.warning("You have not paid yet.")

        if st.button("Logout"):
            auth.logout()
            st.experimental_rerun()

    else:
        menu = st.selectbox("Choose Action", ["Login", "Signup"])

        if menu == "Signup":
            st.subheader("Create a New Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Sign Up"):
                if username and password:
                    success = auth.signup(username, password)
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists. Try another.")
                else:
                    st.error("Please enter username and password.")

        elif menu == "Login":
            st.subheader("Login to Your Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                if username and password:
                    success = auth.login(username, password)
                    if success:
                        st.success(f"Welcome back, {username}!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Please enter username and password.")

if __name__ == "__main__":
    main()
