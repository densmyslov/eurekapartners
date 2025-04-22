import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
from time import sleep
# Import your project files
import login
import auth
import admin_functions as af
import json

# Page config
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Handle login
login.handle_auth()

# Refresh tokens if authenticated
if st.session_state.get("authenticated", False):
    auth.refresh_tokens_if_needed()



if "counter" not in st.session_state:
    st.session_state.counter = 0

def increment_counter():
    st.session_state.counter += 1



# Load logo
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

#=======================================================================================================================================
# LOAD DATA
#=======================================================================================================================================
# Load COI table once into session state
if "coi_df" not in st.session_state:
    st.session_state.coi_df = af.load_coi_table()

# Load default price/qty data ONCE
if "default_price_qty_data" not in st.session_state:
    st.session_state.default_price_qty_data = af.load_default_price_data(counter=st.session_state.counter)
# Editable working copy
if "price_qty_data" not in st.session_state:
    st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()

# Load transactions table
trans_df = af.load_transactions_df(counter=st.session_state.counter)

# Sidebar navigation
section = st.sidebar.radio("Navigate", [
    "COI Management",
    "Token Management"
])

if st.sidebar.button("Refresh"):
    increment_counter()
    af.load_coi_table.clear()
    st.session_state.coi_df = af.load_coi_table(counter=st.session_state.counter)
    st.rerun()

# ==============================
#  COI MANAGEMENT SECTION
# ==============================





# Initialize discard flags
if "discard_price_qty_changes" not in st.session_state:
    st.session_state.discard_price_qty_changes = False

if "price_qty_editor_key" not in st.session_state:
    st.session_state.price_qty_editor_key = "price_qty_editor"

# Handle Discard for price/qty
if st.session_state.discard_price_qty_changes:
    st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()
    st.session_state.price_qty_editor_key = f"price_qty_editor_{st.session_state.counter}"
    st.session_state.discard_price_qty_changes = False

if section == "COI Management":
    st.header("COI Management")

    coi_cols1, coi_cols2 = st.columns(2)

    with coi_cols1.expander("➕ Add New COI"):
        st.subheader("Add New COI")

        # === FORM ===
        with st.form("add_coi"):
            first_name = st.text_input("First Name", value=None)
            last_name = st.text_input("Last Name", value=None)
            email = st.text_input("Email", value=None)
            initial_token_balance = st.number_input("Initial Token Balance", min_value=0)
            access_on = st.toggle("Access On", value=True)
            is_onboarded = st.toggle("Is Onboarded", value=True)
            st.markdown("#### Token Pricing")

            # Editable price/qty table
            price_qty_df = st.data_editor(
                pd.DataFrame(st.session_state.price_qty_data),
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=st.session_state.price_qty_editor_key
            )

            # Update working copy
            st.session_state.price_qty_data = price_qty_df.to_dict(orient="records")

            submitted = st.form_submit_button("Add COI")

            if submitted:
                if any(value is None for value in [first_name, last_name, email]):
                    st.error("Email and First/Last Name cannot be empty.")
                    st.stop()

                # API Call to add COI
                response = af.add_new_coi(
                    first_name,
                    last_name,
                    email,
                    initial_token_balance,
                    st.session_state.price_qty_data,
                    access_on,
                    is_onboarded
                )

                

                if response.status_code == 200:
                    st.success("COI added successfully!")
                    temp_password = json.loads(response.text)['message']
                    st.write(f"Please write down user's temporary password: {temp_password}")

                    # ✅ 1. Reset price_qty_data to default after adding new COI
                    st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()
                    # ✅ 2. Now increment counter
                    increment_counter()
                    # ✅ 3. Reload updated COI table
                    af.load_coi_table.clear()
                    increment_counter()
                    st.session_state.coi_df = af.load_coi_table(counter=st.session_state.counter)
                    sleep(2)
                    # st.rerun()
                else:
                    st.error(f"Error adding COI: {response.text}")

        # --- OUTSIDE form: Discard Price/Qty Changes ---
        st.markdown("---")

        changes_made_price_qty = not price_qty_df.equals(pd.DataFrame(st.session_state.default_price_qty_data))

        if changes_made_price_qty:
            if st.button("❌ Discard Price/Qty Changes"):
                st.session_state.discard_price_qty_changes = True
                st.session_state.counter += 1
                st.rerun()


    # --- Main COI Table Management ---

    if "discard_changes" not in st.session_state:
        st.session_state.discard_changes = False

    if "editor_key" not in st.session_state:
        st.session_state.editor_key = "coi_editor"

    if st.session_state.discard_changes:
        st.session_state.editor_key = f"coi_editor_{st.session_state.counter}"
        st.session_state.discard_changes = False

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

    edited_df = st.data_editor(
        st.session_state.coi_df,
        num_rows="fixed",
        use_container_width=True,
        key=st.session_state.editor_key
    )

    changes_made_coi = not edited_df.equals(st.session_state.coi_df)

    if changes_made_coi:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Changes to S3"):
                try:
                    buffer = BytesIO()
                    edited_df.to_parquet(buffer, index=False)
                    buffer.seek(0)

                    TEMP_TABLE_NAME = "temp/temp_coi_table.parquet"

                    af.S3_CLIENT.put_object(
                        Bucket=af.BUCKET_NAME,
                        Key=TEMP_TABLE_NAME,
                        Body=buffer,
                        ContentType="application/octet-stream"
                    )

                    st.session_state.coi_df = edited_df.copy()
                    st.success("COI Table updated and saved to S3!")
                except Exception as e:
                    st.error(f"Failed to save table: {e}")

        with col2:
            if st.button("❌ Discard COI Table Changes"):
                st.session_state.discard_changes = True
                st.session_state.counter += 1
                st.rerun()

    # Show transactions table
    st.subheader("Transactions")
    st.dataframe(trans_df)

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
