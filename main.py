import streamlit as st
from auth_system import AuthSystem
from history_system import HistorySystem
from image_downloader import ImageDownloader
from stripe_checkout import create_checkout_session
import os
from dotenv import load_dotenv

load_dotenv() 
API_KEY = os.getenv("UNSPLASH_API_KEY")
MAX_IMAGES = 5

auth = AuthSystem()
history = HistorySystem()

downloader = ImageDownloader(api_key=API_KEY)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

if not st.session_state['logged_in']:
    st.title("Login / Signup")
    option = st.radio("Choose action", ("Login", "Signup"))
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Sign Up"):
            if not username or not password:
                st.error("Please enter both fields.")
            elif auth.signup(username.strip(), password.strip()):
                st.success("Account created! You can login now.")
            else:
                st.error("Username already exists.")
    else:
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both fields.")
            elif auth.login(username.strip(), password.strip()):
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")
else:
    username = st.session_state['username']
    st.title(f"Welcome, {username} 👋")

    if st.button("Logout"):
        auth.logout()
        st.experimental_rerun()

    st.markdown("---")
    count = history.get_image_count(username)
    paid = auth.is_paid(username)

    st.markdown(f"**🖼️ Images generated:** `{count}` {'(Unlimited)' if paid else f'/ {MAX_IMAGES}'}")
    if not paid:
        st.progress(min(count / MAX_IMAGES, 1.0))

    st.subheader("Search Image from Unsplash")
    query = st.text_input("Type a keyword (e.g. handbag, perfume)")

    if st.button("Generate Image") and query.strip():
        if count >= MAX_IMAGES and not paid:
            st.warning("You reached your image generation limit.")
            if "checkout_url" not in st.session_state:
                if st.button("Upgrade to Premium ($2.00)"):
                    url = create_checkout_session()
                    st  .session_state.checkout_url = url
                    st.experimental_rerun() 
            else:
                url = st.session_state.checkout_url
                st.markdown(f"[Click here to Pay via Stripe]({url})", unsafe_allow_html=True)
        else:
            file = downloader.download_images(query.strip())
            if file:
                st.image(file)
                with open(file, "rb") as f:
                    st.download_button("Download Image", data=f, file_name=file.split('/')[-1])
                history.add_record(username, query.strip())
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("Your Search History")
    history_data = history.get_history(username)
    if history_data:
        for rec_id, q, date in history_data:
            col1, col2, col3 = st.columns([3, 3, 1])
            col1.write(q)
            col2.write(date)
            if col3.button("Delete", key=f"del_{rec_id}"):
                history.delete_record(rec_id)
                st.experimental_rerun()
    else:
        st.info("No search history found.")

    params = st.experimental_get_query_params()
    if "success" in params:
        st.success("Payment successful! Premium features unlocked.")
        auth.mark_paid(username)
        st.experimental_set_query_params()  # Clear URL
        st.experimental_rerun()
    