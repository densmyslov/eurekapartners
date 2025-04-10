import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

# Import your project files
import login
import auth
import admin_functions as af

# Page config
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Handle login
login.handle_auth()

# Refresh tokens if authenticated
if st.session_state.get("authenticated", False):
    auth.refresh_tokens_if_needed()

# Load COI table once into session state
if "coi_df" not in st.session_state:
    st.session_state.coi_df = af.load_coi_table()

# Load and display your logo
image = Image.open("assets/eureka_logo.jpeg")
buffered = BytesIO()
image.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()
st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{img_b64}" width="40" style="margin-right: 10px;">
        <h1 style="margin: 0;">Eureka Partners Admin Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# Sidebar navigation
section = st.sidebar.radio("Navigate", [
    "COI Management",
    "Token Management"
])

if st.sidebar.button("Refresh"):
    af.load_coi_table.clear()
    st.session_state.coi_df = af.load_coi_table()
    st.rerun()
    

# ==============================
#  COI MANAGEMENT SECTION
# ==============================

if section == "COI Management":
    st.header("COI Management")

    coi_cols1, coi_cols2 = st.columns(2)

    with coi_cols1.expander("➕ Add / Update COI"):
        st.subheader("Add New COI")

        with st.form("add_coi"):
            full_name = st.text_input("Full Name", value=None)
            email = st.text_input("Email", value=None)
            initial_tokens = st.number_input("Initial Token Balance", min_value=0)
            initial_price = st.slider("Initial Token Price", value=10, min_value=1, max_value=100)
            access_on = st.toggle("Access On", value=True)
            is_onboarded = st.toggle("Is Onboarded", value=True)

            submitted = st.form_submit_button("Add COI")

            if submitted:
                if not email or not full_name:
                    st.error("Email and Full Name cannot be empty.")
                    st.stop()

                # API Call to add COI
                response = af.add_new_coi(full_name, email, initial_tokens, initial_price, access_on, is_onboarded)

                if response.status_code == 200:
                    st.success("COI added successfully!")

                    # ⬇️ Reload latest table from S3 immediately
                    af.load_coi_table.clear()
                    st.session_state.coi_df = af.load_coi_table()

                else:
                    st.error(f"Error adding COI: {response.text}")

    with coi_cols2.expander("🗑️ Delete COI"):
        st.subheader("Delete COI(s)")

        with st.form("delete_coi"):
            emails = st.text_area("Add emails separated by newlines", placeholder="email1@example.com\nemail2@example.com")
            submitted = st.form_submit_button("Delete COI")

            if submitted:
                if not emails.strip():
                    st.error("Emails cannot be empty.")
                    st.stop()

                email_list = emails.strip().split("\n")
                # API Call to delete COI(s)
                response = af.delete_coi(email_list)

                if response.status_code == 200:
                    st.success("COI(s) deleted successfully!")

                    # ⬇️ Reload latest table from S3 immediately
                    af.load_coi_table.clear()
                    st.session_state.coi_df = af.load_coi_table()

                else:
                    st.error(f"Error deleting COI: {response.text}")

    # --- Editable Data Editor ---
    edited_df = st.data_editor(
        st.session_state.coi_df,
        num_rows="dynamic",
        use_container_width=True,
        key="coi_editor"
    )

    # --- Save Button (Save only if there are changes) ---
    if not edited_df.equals(st.session_state.coi_df):
        if st.button("💾 Save Changes to S3"):
            try:
                buffer = BytesIO()
                edited_df.to_parquet(buffer, index=False)
                buffer.seek(0)

                af.S3_CLIENT.put_object(
                    Bucket=af.BUCKET_NAME,
                    Key=af.COI_TABLE_NAME,
                    Body=buffer,
                    ContentType="application/octet-stream"
                )

                # ✅ Update session state with edited version
                st.session_state.coi_df = edited_df.copy()

                st.success("COI Table updated and saved to S3!")

            except Exception as e:
                st.error(f"Failed to save table: {e}")

# ==============================
#  TOKEN MANAGEMENT SECTION
# ==============================

elif section == "Token Management":
    st.header("Token Management")

    st.subheader("Edit Tokens Manually")
    with st.form("edit_tokens"):
        email = st.selectbox("Select User", st.session_state.coi_df["email"], key="edit_tokens_user")
        tokens = st.number_input("Adjust Token Count", value=0)
        st.form_submit_button("Update Tokens")

    st.subheader("Token Usage Logs")
    token_logs = pd.DataFrame([
        {"User": "user1@example.com", "Action": "Used 20 tokens", "Date": "2024-03-29"},
        {"User": "user2@example.com", "Action": "Refund request", "Date": "2024-03-28"},
    ])
    st.dataframe(token_logs)

    st.subheader("Refund Requests")
    refund_user = st.selectbox("Select User Requesting Refund", st.session_state.coi_df["email"], key="refund_user")
    st.text_area("Reason for Refund")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Approve Refund")
    with col2:
        st.button("Deny Refund")
