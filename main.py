import streamlit as st
from auth_system import AuthSystem
from history_system import HistorySystem
from image_downloader import ImageDownloader
from dotenv import load_dotenv
import stripe
import os
from datetime import datetime

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or "sk_test_..."  
API_KEY = os.getenv("UNSPLASH_API_KEY")
MAX_IMAGES = 5

def rerun():
    st.rerun()

auth = AuthSystem()
history = HistorySystem()
downloader = ImageDownloader(api_key=API_KEY)

# Session state setup
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

if 'last_image' not in st.session_state:
    st.session_state['last_image'] = None

# If not logged in, show login/signup
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
                st.session_state['logged_in'] = True
                st.session_state['username'] = username.strip()
                st.success("Login successful!")
                rerun()
            else:
                st.error("Invalid credentials.")
else:
    username = st.session_state['username']
    st.title(f"Welcome, {username} 👋")

    if st.button("Logout"):
        auth.logout()
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['last_image'] = None
        rerun()

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

            # Show payment button
            if "checkout_url" not in st.session_state:
                if st.button("Upgrade to Premium ($2.00)"):
                    session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {'name': 'Premium Access'},
                                'unit_amount': 200,
                            },
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url='http://localhost:8501/?success=true',
                        cancel_url='http://localhost:8501/?canceled=true',
                    )
                    st.session_state.checkout_url = session.url
                    rerun()
            else:
                url = st.session_state.checkout_url
                st.markdown(f"[Click here to Pay via Stripe]({url})", unsafe_allow_html=True)

        else:
            # Clear old image before downloading new
            st.session_state['last_image'] = None
            file = downloader.download_images(query.strip())
            if file:
                st.session_state['last_image'] = file
                history.add_record(username, query.strip())
                # Do not rerun here to keep image visible

    # Display image if exists
    if st.session_state['last_image']:
        st.image(st.session_state['last_image'])
        with open(st.session_state['last_image'], "rb") as f:
            st.download_button("Download Image", data=f, file_name=os.path.basename(st.session_state['last_image']))

    # Handle success/cancel message from URL
    query_params = st.experimental_get_query_params()
    if "success" in query_params:
        st.success("Payment successful! 🎉 Please refresh or log in again to continue.")
    elif "canceled" in query_params:
        st.warning("Payment was canceled.")

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
                rerun()
    else:
        st.info("No search history found.")
