import streamlit as st
import pandas as pd
from io import BytesIO
from time import sleep
import json
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





# Load logo
logo = af.load_logo()
st.markdown(f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo}" width="40" style="margin-right: 10px;">
        <h1 style="margin: 0;">Eureka Partners Admin Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

#====================================BUTTON COLOR======================
st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #4CAF50;  /* Green */
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)

#====================================================================================================================
# INITIALIZE SESSION STATES
#====================================================================================================================

if "counter" not in st.session_state:
    st.session_state.counter = 0


# Load default price/qty data ONCE
if "default_price_qty_data" not in st.session_state:
    st.session_state.default_price_qty_data = af.load_default_price_data(counter=st.session_state.counter)
# Editable working copy
if "price_qty_data" not in st.session_state:
    st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()

# Initialize discard flags
if "discard_price_qty_changes" not in st.session_state:
    st.session_state.discard_price_qty_changes = False

if "price_qty_editor_key" not in st.session_state:
    st.session_state.price_qty_editor_key = "price_qty_editor"

#=======================================================================================================================================
# LOAD DATA
#=======================================================================================================================================
# Load COI table once into session state
if "coi_df" not in st.session_state:
    st.session_state.coi_df = af.load_coi_table()

# Load transactions table
trans_df = af.load_transactions_df(counter=st.session_state.counter)

if st.sidebar.button("Refresh"):
    af.increment_counter()
    af.load_coi_table.clear()
    st.session_state.coi_df = af.load_coi_table(counter=st.session_state.counter)
    trans_df = af.load_transactions_df(counter=st.session_state.counter)
    st.rerun()






# Handle Discard for price/qty
if st.session_state.discard_price_qty_changes:
    st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()
    st.session_state.price_qty_editor_key = f"price_qty_editor_{st.session_state.counter}"
    st.session_state.discard_price_qty_changes = False

#=================================================================================
#  COI MANAGEMENT SECTION
#=================================================================================


col1, col2 = st.columns(2)
col1.subheader(":blue[Adjust COI tokens]")

with col1.expander("expand to adjust COI tokens"):
    with st.form("edit_tokens"):
        email = st.selectbox("Select User", st.session_state.coi_df["email"], key="edit_tokens_user")
        num_tokens = st.number_input("Adjust Token Count", value=0)
        if st.form_submit_button("Update Tokens"):
            email_hash = st.session_state.coi_df.query("email==@email")['email_hash'].tolist()[0]
            coi_id = st.session_state.coi_df.query("email==@email")['uid'].tolist()[0]
            payload={
            'action': 'update transactions_df.parquet',
            'coi_email': email,
            'email_hash': email_hash,
            'coi_id':coi_id,
            'num_tokens': num_tokens,
            'transaction_type': "Token adjustment"
            }
            api_url = "https://kbeopzaocc.execute-api.us-east-1.amazonaws.com/prod/adjust-tokens"
            r = af.safe_api_post(api_url, payload)
            st.write(r)
        

st.subheader(":blue[Add/Delete COI]")
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
                st.badge(temp_password, color="green")

                # ✅ 1. Reset price_qty_data to default after adding new COI
                st.session_state.price_qty_data = st.session_state.default_price_qty_data.copy()
                # ✅ 2. Now increment counter
                af.increment_counter()
                # ✅ 3. Reload updated COI table
                af.load_coi_table.clear()
                st.session_state.coi_df = af.load_coi_table(counter=st.session_state.counter)
                sleep(2)
                st.rerun()
            else:
                st.error(f"Error adding COI: {response.text}")

    # --- OUTSIDE form: Discard Price/Qty Changes ---
    st.markdown("---")

    changes_made_price_qty = not price_qty_df.equals(pd.DataFrame(st.session_state.default_price_qty_data))

    if changes_made_price_qty:
        if st.button("❌ Discard Price/Qty Changes"):
            st.session_state.discard_price_qty_changes = True
            af.increment_counter()
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

st.subheader(":blue[COI Table]")
with st.expander("Expand to see table"):

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
st.subheader(":blue[Transactions]")
with st.expander("Expand to see transactions"):
    st.dataframe(trans_df)


