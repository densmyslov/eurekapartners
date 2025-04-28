import streamlit as st
import pandas as pd
from io import BytesIO
from time import sleep
import json
import uuid
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



s3_client = af.S3_CLIENT

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

if "discard_changes" not in st.session_state:
    st.session_state.discard_changes = False

if "editor_key" not in st.session_state:
    st.session_state.editor_key = "coi_editor"

# Initialize session state variables if they don't exist
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
    st.session_state.emails_to_delete = []

if 'changes_made_coi' not in st.session_state:
    st.session_state.changes_made_coi = False

if 'update_default_settings' not in st.session_state:
    st.session_state.update_default_settings = False

if 'update_defaults' not in st.session_state:
    st.session_state.update_defaults = False

#=======================================================================================================================================
# LOAD DATA
#=======================================================================================================================================
# Load COI table once into session state
if "coi_df" not in st.session_state:
    st.session_state.coi_df = af.load_coi_table(counter = st.session_state.counter)

# Load transactions table
trans_df = af.load_transactions_df(counter=st.session_state.counter)

if "default_banks_df" not in st.session_state:
    st.session_state.default_banks_df = af.load_default_banks_df(counter=st.session_state.counter)


#=======================================================================================================================================
# REFRESH COI_DF AND TRANS_DF
#=======================================================================================================================================

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
#  ADJUST DEFAULT SETTINGS
#=================================================================================

with st.sidebar.expander("Adjust default settings"):


    if "price_qty_data" not in st.session_state:
        st.session_state.price_qty_data = af.load_default_price_data(counter=st.session_state.counter)
    if "default_banks_df" not in st.session_state:
        st.session_state.default_banks_df = af.load_default_banks_df(counter=st.session_state.counter)

    # Backup copies
    if "initial_price_qty_data" not in st.session_state:
        st.session_state.initial_price_qty_data = st.session_state.price_qty_data.copy()
    if "initial_banks_df" not in st.session_state:
        st.session_state.initial_banks_df = st.session_state.default_banks_df.copy()

    # Track editor keys
    if "editor_keys" not in st.session_state:
        st.session_state.editor_keys = {
            "price": str(uuid.uuid4()),
            "banks": str(uuid.uuid4())
        }

    def reset_to_initial():
        st.session_state.price_qty_data = st.session_state.initial_price_qty_data.copy()
        st.session_state.default_banks_df = st.session_state.initial_banks_df.copy()
        st.session_state.editor_keys["price"] = str(uuid.uuid4())
        st.session_state.editor_keys["banks"] = str(uuid.uuid4())
        st.rerun()

    with st.sidebar.expander("Adjust default settings"):

        price_qty_df_default = st.data_editor(
            pd.DataFrame(st.session_state.price_qty_data),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key=st.session_state.editor_keys["price"]
        )

        banks_df_default = st.data_editor(
            pd.DataFrame(st.session_state.default_banks_df),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key=st.session_state.editor_keys["banks"]
        )

        
            
        payload = {}
        if not price_qty_df_default.equals(pd.DataFrame(st.session_state.price_qty_data)):
            payload["price_qty_data"] = price_qty_df_default.to_dict(orient="records")
        if not banks_df_default.equals(pd.DataFrame(st.session_state.default_banks_df)):
            payload["banks_df"] = banks_df_default.to_dict(orient="records")
            
        if payload:
                st.warning("You are going to update:")
                st.write(payload)
                st.session_state.update_default_settings = True
                st.session_state.default_payload = payload

        col1, col2 = st.columns(2)
        # if st.session_state.update_default_settings:
        #     if st.button("Update default settings"):
        #         st.session_state.update_defaults = True
               
            
        with col1:
                if st.button("Confirm Update"):
                    payload = st.session_state.default_payload
                    if "price_qty_data" in payload:
                        st.session_state.price_qty_data = payload["price_qty_data"]
                    if "banks_df" in payload:
                        st.session_state.default_banks_df = payload["banks_df"]

                    # Update initial copies
                    st.session_state.initial_price_qty_data = st.session_state.price_qty_data.copy()
                    st.session_state.initial_banks_df = st.session_state.default_banks_df.copy()



                    if "price_qty_data" in payload:
                        buffer = BytesIO()
                        pd.DataFrame(payload["price_qty_data"]).to_parquet(buffer, index=False)
                        buffer.seek(0)
                        st.session_state.price_qty_data = payload["price_qty_data"]
                        s3_client.put_object(
                            Bucket=af.BUCKET_NAME,
                            Key = af.DEFAULT_TOKEN_PRICES_DF_NAME,
                            Body=buffer.getvalue()
                        )
                    if "banks_df" in payload:
                        buffer = BytesIO()
                        pd.DataFrame(payload["banks_df"]).to_parquet(buffer, index=False)
                        buffer.seek(0)
                        st.session_state.default_banks_df = payload["banks_df"]
                        s3_client.put_object(
                            Bucket=af.BUCKET_NAME,
                            Key = af.DEFAULT_BANKS_DF_NAME,
                            Body=buffer.getvalue()
                        )
                    st.session_state.update_default_settings = False
                    sleep(3)
                    st.success("Updated")
                    st.rerun()



        with col2:
                    if st.button("Cancel Update"):
                        reset_to_initial()
                        st.session_state.update_default_settings = False            
                        st.rerun()








#=================================================================================
#  ADJUST COI TOKENS
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
        
#=================================================================================
#  ADD NEW COI
#=================================================================================

coi_cols1, coi_cols2 = st.columns(2)
coi_cols1.subheader(":blue[Add New COI]")
with coi_cols1.expander("➕ expand to add a new COI"):

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
                # sleep(2)
                # st.rerun()
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



if st.session_state.discard_changes:
    st.session_state.editor_key = f"coi_editor_{st.session_state.counter}"
    st.session_state.discard_changes = False

#=================================================================================
#  DELETE COI
#=================================================================================

coi_cols2.subheader(":red[Delete COI]")
with coi_cols2.expander("🗑️ expand to delete COI"):
    


    # --- Confirmation Section (Displayed only when confirmation is pending) ---
    if st.session_state.confirm_delete:
        st.warning(f"**Confirm Deletion:** Are you sure you want to delete COIs for the following {len(st.session_state.emails_to_delete)} email(s)? This action cannot be undone.")

        # Display the emails again for clarity during confirmation
        st.text_area("Emails targeted for deletion:", value="\n".join(st.session_state.emails_to_delete), height=150, disabled=True)

        # Create columns for confirmation buttons
        col1, col2, col3 = st.columns([3, 2, 3]) # Adjust ratios as needed

        with col1:
            if st.button(":red[Delete]", type="primary"):
                try:
                    # Retrieve the list from session state
                    email_list = st.session_state.emails_to_delete

                    # --- Perform the actual API Call ---
                    # st.info(f"Attempting to delete COIs for: {', '.join(email_list)}") # Optional: Add for debugging
                    response = af.delete_coi(email_list) # Use the list stored in state

                    if response.status_code == 200:
                        st.success("COI(s) deleted successfully!")
                        sleep(3)

                        # ⬇️ Reload latest table from S3 immediately
                        af.load_coi_table.clear() # Assuming this clears a cache like st.cache_data or st.cache_resource
                        # Ensure the key used for storing df matches where you use it elsewhere
                        st.session_state.coi_df = af.load_coi_table()

                    else:
                        st.error(f"Error deleting COI: {response.text}")

                except Exception as e:
                    st.error(f"An unexpected error occurred during deletion: {e}")

                finally:
                    # --- Reset state regardless of success or failure ---
                    st.session_state.confirm_delete = False
                    st.session_state.emails_to_delete = []
                    st.rerun() # Rerun to clear the confirmation UI and show the form again

        with col3:
            if st.button("Cancel"):
                st.info("Deletion cancelled.")
                # --- Reset state ---
                st.session_state.confirm_delete = False
                st.session_state.emails_to_delete = []
                st.rerun() # Rerun to clear the confirmation UI

    # --- Original Form Section (Displayed only when NOT confirming) ---
    # Hide the form if confirmation is pending
    if not st.session_state.confirm_delete:
        with st.form("delete_coi"):
            st.subheader("Delete COI Entries") # Added a subheader for clarity
            emails = st.text_area("Enter emails separated by newlines", placeholder="email1@example.com\nemail2@example.com")
            submitted = st.form_submit_button(":red[Prepare Deletion...]") # Changed button text slightly

            if submitted:
                # Basic validation
                if not emails.strip():
                    st.error("Emails cannot be empty.")
                    # No st.stop() needed here, just let the form finish without proceeding
                else:
                    # Prepare list and store in session state for confirmation
                    email_list = [email.strip() for email in emails.strip().split("\n") if email.strip()] # Clean up list

                    if not email_list:
                        st.error("No valid emails entered after stripping whitespace.")
                    else:
                        st.session_state.emails_to_delete = email_list
                        st.session_state.confirm_delete = True # Set flag to trigger confirmation UI
                        st.rerun() # Rerun immediately to show the confirmation section
#=================================================================================
#  COI TABLE
#=================================================================================

st.subheader(":blue[COI Table]")
with st.expander("Expand to see table"):

    edited_df = st.data_editor(
        st.session_state.coi_df,
        num_rows="fixed",
        use_container_width=True,
        key=st.session_state.editor_key
    )

    st.session_state.changes_made_coi = not edited_df.equals(st.session_state.coi_df)
    # changes_made_coi = not edited_df.equals(st.session_state.coi_df)

    if st.session_state.changes_made_coi:
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

                    # st.session_state.coi_df = edited_df.copy()
                    st.success("COI Table updated and saved to S3!")
                    # sleep(5)
                    # st.rerun()
                    cols = ['uid','email','first_name','last_name','access_on']
                    df = edited_df[cols].copy()
                    df = pd.concat([st.session_state.coi_df[cols], df]).drop_duplicates(keep=False)
                    payload = df.iloc[-1,:].to_dict()
                    st.write(payload)
                    api_url = "https://xuyzj7f0zd.execute-api.us-east-1.amazonaws.com/prod/change-coi-data"
                    response = af.safe_api_post(api_url, payload)
                    st.write(response)
                    st.session_state.changes_made_coi = False
                    st.session_state.changes_made_coi = False
                    sleep(3)
                    af.reload(coi_df=True)
 
                except Exception as e:
                    st.error(f"Failed to save table: {e}")
                


        with col2:
            if st.session_state.changes_made_coi:
                st.write(st.session_state.changes_made_coi)

                if st.button("❌ Discard COI Table Changes"):
                    st.session_state.discard_changes = True
                    st.session_state.counter += 1
                    st.rerun()

#=================================================================================
#  TRANSACTIONS TABLE
#=================================================================================
st.subheader(":blue[Transactions]")
with st.expander("Expand to see transactions"):
    st.dataframe(trans_df)


