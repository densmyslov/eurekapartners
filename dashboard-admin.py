import streamlit as st
import pandas as pd
import requests
from PIL import Image
import base64
from io import BytesIO
from time import sleep
import boto3
from io import BytesIO
# import py files
import auth

import admin_functions as af

st.set_page_config(page_title="Admin Dashboard", layout="wide")
import login





# auth.handle_auth()
login.handle_auth()






coi_df = af.load_coi_table()



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






# simulated data
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
    coi_table_container = st.container()
    coi_table_container.dataframe(coi_df)

    
    coi_cols1, coi_cols2, coi_cols3 = st.columns(3)
    with coi_cols1.expander("Add new / updateCOI"):


#============================================ADD NEW COI===============================================
        st.subheader("Add New COI")
        with st.form("add_coi"):
            full_name = st.text_input("Full Name", value=None)
            email = st.text_input("email", value=None)
            initial_tokens = st.number_input("Initial Token Balance", min_value=0)
            initial_price = st.slider("Initial Token Price", value=10, min_value=1, max_value=100)
            access_on = st.toggle("Access On", value=True)

            submitted = st.form_submit_button("Add COI")

            if submitted:
                if not email or not full_name:
                    # Show an error message and stop execution
                    st.error("Email and Full Name cannot be empty.")
                    st.stop()


                response = af.add_new_coi(full_name, email, initial_tokens, initial_price, access_on)
                af.update_coi_df_on_submit(coi_df, response, coi_table_container)


    with coi_cols2.expander("Delete COI"):
        st.warning("to delete COI: add email -> ENTER -> add another email ... -> Delete COI")
        with st.form("delete_coi"):
            emails = st.text_area("add email, click enter, add another one if needed", placeholder=None)
            submitted = st.form_submit_button("Delete COI")
            if submitted:
                if not emails:
                    st.error("Emails cannot be empty.")
                    st.stop()
                # try:
                response = af.delete_coi(emails)
                af.update_coi_df_on_submit(coi_df, response, coi_table_container)

                # except Exception as e:
                #     st.error(f"Request failed: {e}")
            

    edited_df = st.data_editor(
        coi_df,
        num_rows="dynamic",  # Allow adding new rows
        use_container_width=True,
        key="coi_editor"
    )            

    if st.button("Save Changes to S3"):
        try:
            # Convert the edited DataFrame to a parquet file
            buffer = BytesIO()
            edited_df.to_parquet(buffer, index=False)
            buffer.seek(0)

            # Upload to S3
            af.S3_CLIENT.put_object(
                Bucket=af.BUCKET_NAME,
                Key=af.COI_TABLE_NAME,
                Body=buffer,
                ContentType="application/octet-stream"
            )
            st.success("COI Table updated successfully!")

        except Exception as e:
            st.error(f"Failed to save table: {e}")

        

    # st.subheader("All Users")
    # st.dataframe(coi_df)

    # st.subheader("Modify User")
    # selected_email = st.selectbox("Select User", coi_df["email"])
    # col1, col2, col3 = st.columns(3)

    # with col1:
    #     st.checkbox("Active", value=coi_df[coi_df["email"] == selected_email]["Active"].iloc[0])
    # with col2:
    #     st.number_input("Token Balance", value=int(coi_df[coi_df["email"] == selected_email]["Tokens"].iloc[0]))
    # with col3:
    #     st.text_input("Referral Account", value=coi_df[coi_df["email"] == selected_email]["Referral"].iloc[0])

    # st.button("Save Changes")

    # st.subheader("Referral Performance")
    # st.text("Coming soon: Referral performance dashboard.")

elif section == "Token Management":
    st.header("Token Management")

    st.subheader("Edit Tokens Manually")
    with st.form("edit_tokens"):
        email = st.selectbox("Select User", coi_df["email"], key="edit_tokens_user")
        tokens = st.number_input("Adjust Token Count", value=0)
        st.form_submit_button("Update Tokens")

    st.subheader("Token Usage Logs")
    st.dataframe(token_logs)

    st.subheader("Refund Requests")
    refund_user = st.selectbox("Select User Requesting Refund", coi_df["email"], key="refund_user")
    st.text_area("Reason for Refund")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Approve Refund")
    with col2:
        st.button("Deny Refund")
