import streamlit as st

def handle_auth():
    """
    Displays a login form if the user is not authenticated.
    Once authenticated, shows a "Sign Out" button.
    The credentials are compared against those stored in st.secrets.
    """

    # Initialize session state for authentication if not already set.
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If the user is authenticated, display a "Sign Out" button.
    if st.session_state.authenticated:
        if st.button("Sign Out"):
            st.session_state.clear()
            st.experimental_rerun()

    # If the user is not authenticated, display the login form.
    if not st.session_state.authenticated:
        st.title("Please Log In")
        st.write("Enter your email and password to access the app.")

        # Create columns to center the form and limit its width
        left_col, center_col, right_col = st.columns([1, 2, 1])

        with left_col:
            with st.form("login_form"):
                email_input = st.text_input("Email")
                password_input = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Log In")

            if submit_button:
                # Retrieve the valid credentials from st.secrets.
                valid_email = st.secrets["credentials"]["email"]
                valid_password = st.secrets["credentials"]["password"]

                # Validate the credentials.
                if email_input == valid_email and password_input == valid_password:
                    st.session_state.authenticated = True
                    st.success("Logged in successfully!")
                    st.experimental_rerun()  # Rerun the app to load authenticated content.
                else:
                    st.error("Invalid email or password. Please try again.")

        # Stop further execution until the user is authenticated.
        st.stop()

# Run the authentication logic.
handle_auth()

# Authenticated content goes below.
st.write("Welcome to your secure Streamlit app!")
