import streamlit as st
import stripe
import os

# Set your Stripe Secret key here or in .env
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or "sk_test_..."  # Replace with your key

MAX_FREE = 3

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.paid = False
    st.session_state.image_count = 0

def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Premium Access'},
                'unit_amount': 200,  # $2.00 in cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:8501/?success=true',
        cancel_url='http://localhost:8501/?canceled=true',
    )
    return session.url

def login_screen():
    st.title("Login")
    username = st.text_input("Username")
    if st.button("Login"):
        if username.strip():
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.experimental_rerun()
        else:
            st.error("Enter username")

def main_screen():
    st.title(f"Welcome, {st.session_state.username}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.paid = False
        st.session_state.image_count = 0
        st.experimental_rerun()

    st.write(f"Images generated: {st.session_state.image_count} / {'Unlimited' if st.session_state.paid else MAX_FREE}")

    if st.session_state.paid:
        st.success("You have premium access! Generate unlimited images.")
    else:
        st.info("Free users can generate up to 3 images.")

    query = st.text_input("Search image (dummy):")

    if st.button("Generate Image") and query.strip():
        if not st.session_state.paid and st.session_state.image_count >= MAX_FREE:
            st.warning("Limit reached! Please upgrade to premium.")

            if "checkout_url" not in st.session_state:
                if st.button("Upgrade to Premium ($2)"):
                    url = create_checkout_session()
                    st.session_state.checkout_url = url
                    st.experimental_rerun()
            else:
                url = st.session_state.checkout_url
                st.markdown(f"[Pay via Stripe]({url})", unsafe_allow_html=True)

                if "opened_checkout" not in st.session_state:
                    js = f"<script>window.open('{url}', '_blank')</script>"
                    st.markdown(js, unsafe_allow_html=True)
                    st.session_state.opened_checkout = True
        else:
            st.success(f"Image generated for query: {query}")
            st.session_state.image_count += 1

params = st.experimental_get_query_params()

if "success" in params:
    st.session_state.paid = True
    st.experimental_set_query_params()
    st.success("Payment successful! Premium unlocked.")
elif "canceled" in params:
    st.experimental_set_query_params()
    st.warning("Payment canceled.")

if not st.session_state.logged_in:
    login_screen()
else:
    main_screen()
