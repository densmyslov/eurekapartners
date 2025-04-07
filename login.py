import streamlit as st
import auth  # <-- we import our auth.py functions here

def handle_auth():
    """
    Handles local Streamlit login form and authentication with Cognito.
    """

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        if st.sidebar.button("Sign Out", key="signout_button"):
            st.session_state.clear()
            st.rerun()

    if not st.session_state.authenticated:
        st.title("Please Log In")
        st.write("Enter your email and password to access the app.")

        left_col, center_col, right_col = st.columns([3, 2, 3])

        with center_col:
            with st.form("login_form"):
                email_input = st.text_input("Email")
                password_input = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Log In")

            if submit_button:
                # First check against local Streamlit secrets (optional)
                valid_email = st.secrets["credentials"]["email"]
                valid_password = st.secrets["credentials"]["password"]

                if email_input == valid_email and password_input == valid_password:
                    # Call Cognito AdminInitiateAuth
                    success = auth.get_tokens_directly_admin_auth(email_input, password_input)
                    if success:
                        st.session_state.authenticated = True
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Authentication failed.")
                else:
                    st.error("Invalid email or password. Please try again.")

        st.stop()  # Prevent the rest of the app from loading if not logged in






