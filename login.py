import streamlit as st

def handle_auth():
    """
    Displays a login form if the user is not authenticated.
    Once authenticated, shows a "Sign Out" button.
    """

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # AUTHENTICATED BLOCK
    if st.session_state.authenticated:
        # Dynamically generate a key based on session state
        if st.sidebar.button("Sign Out", key=f"signout_button_{st.session_state.authenticated}"):
            st.session_state.clear()
            st.rerun()

    # NOT AUTHENTICATED BLOCK
    if not st.session_state.authenticated:
        st.title("Please Log In")
        st.write("Enter your email and password to access the app.")

        # Center the form nicely
        left_col, center_col, right_col = st.columns([3, 2, 3])

        with center_col:
            with st.form("login_form"):
                email_input = st.text_input("Email")
                password_input = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Log In")

            if submit_button:
                valid_email = st.secrets["credentials"]["email"]
                valid_password = st.secrets["credentials"]["password"]

                if email_input == valid_email and password_input == valid_password:
                    st.session_state.authenticated = True
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")

        st.stop()

# Always call authentication at the top
handle_auth()

# Protected content goes here
st.write("Welcome to the secure Admin Dashboard!")
