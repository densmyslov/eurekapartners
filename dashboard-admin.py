import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
import auth

st.set_page_config(page_title="Admin Dashboard", layout="wide")
# Load the image
image = Image.open("assets/eureka_logo.jpeg")

# Convert to base64
buffered = BytesIO()
image.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()
st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{img_b64}" width="40" style="margin-right: 10px;">
        <h1 style="margin: 0;">Eureka Partners Admin Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

auth.handle_auth()




# Simulated user and token data
user_data = pd.DataFrame([
    {"Email": "user1@example.com", "Active": True, "Tokens": 120, "Referral": "ref_001"},
    {"Email": "user2@example.com", "Active": False, "Tokens": 80, "Referral": "ref_002"},
])
token_logs = pd.DataFrame([
    {"User": "user1@example.com", "Action": "Used 20 tokens", "Date": "2024-03-29"},
    {"User": "user2@example.com", "Action": "Refund request", "Date": "2024-03-28"},
])

section = st.sidebar.radio("Navigate", [
    "COI Management",
    "Token Management"
])



if section == "COI Management":
    st.header("COI Management")

    st.subheader("Add New COI")
    with st.form("add_coi"):
        st.text_input("Full Name")
        st.text_input("Email")
        st.number_input("Initial Token Balance", min_value=0)
        st.slider("Initial Token Price", value=10, min_value=1, max_value=100)
        st.form_submit_button("Add COI")

    st.subheader("All Users")
    st.dataframe(user_data)

    st.subheader("Modify User")
    selected_email = st.selectbox("Select User", user_data["Email"])
    col1, col2, col3 = st.columns(3)

    with col1:
        st.checkbox("Active", value=user_data[user_data["Email"] == selected_email]["Active"].iloc[0])
    with col2:
        st.number_input("Token Balance", value=int(user_data[user_data["Email"] == selected_email]["Tokens"].iloc[0]))
    with col3:
        st.text_input("Referral Account", value=user_data[user_data["Email"] == selected_email]["Referral"].iloc[0])

    st.button("Save Changes")

    st.subheader("Referral Performance")
    st.text("Coming soon: Referral performance dashboard.")

elif section == "Token Management":
    st.header("Token Management")

    st.subheader("Edit Tokens Manually")
    with st.form("edit_tokens"):
        email = st.selectbox("Select User", user_data["Email"], key="edit_tokens_user")
        tokens = st.number_input("Adjust Token Count", value=0)
        st.form_submit_button("Update Tokens")

    st.subheader("Token Usage Logs")
    st.dataframe(token_logs)

    st.subheader("Refund Requests")
    refund_user = st.selectbox("Select User Requesting Refund", user_data["Email"], key="refund_user")
    st.text_area("Reason for Refund")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Approve Refund")
    with col2:
        st.button("Deny Refund")
