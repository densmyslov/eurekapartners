import requests
import streamlit as st
import pandas as pd
from io import BytesIO
from time import sleep
import boto3
import json

S3_ACCESS_KEY = st.secrets["s3"]["S3_ACCESS_KEY"]
S3_SECRET_KEY = st.secrets["s3"]["S3_SECRET_KEY"]
S3_CLIENT = boto3.client('s3',
            aws_access_key_id = S3_ACCESS_KEY,
            aws_secret_access_key = S3_SECRET_KEY)
BUCKET_NAME = st.secrets["s3"]["BUCKET_NAME"]
COI_TABLE_NAME = st.secrets["s3"]["COI_TABLE_NAME"]

def add_new_coi(full_name, email, initial_tokens, initial_price, access_on):
    """
    Adds a new COI to the database.

    Parameters:
    - full_name (str): Full name of the COI.
    - email (str): Email address of the COI.
    - initial_tokens (int): Initial token balance for the COI.
    - initial_price (float): Initial token price for the COI.
    - access_on (bool): Access status.
    """
    cognito_jwt_token = st.session_state.get("id_token")  # authorization token
    # st.write("JWT Token:", cognito_jwt_token)


    api_url = "https://xuyzj7f0zd.execute-api.us-east-1.amazonaws.com/prod/add-coi"
    headers = {
        "Authorization": f"Bearer {cognito_jwt_token}",  # <-- FIX HERE
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "full_name": full_name,
        "token_balance": initial_tokens,
        "token_price": initial_price,
        "access_on": access_on
    }
    return requests.post(api_url, json=data, headers=headers)

def delete_coi(emails):
    """
    Deletes a COI from the database.

    Parameters:
    - email (list of str): Email addresses of the COI to delete.
    """
    st.write(f"emails: {emails}")
    cognito_jwt_token = st.session_state.get("id_token") # authorization token
    api_url = "https://7893kaawd5.execute-api.us-east-1.amazonaws.com/prod/delete-coi"
    headers = {
        "Authorization": cognito_jwt_token,
        "Content-Type": "application/json"
    }
    data = {
        "emails": emails
    }
    return requests.post(api_url, json=data, headers=headers)

@st.cache_data(show_spinner="Loading COI Table...")
def load_coi_table():
    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=COI_TABLE_NAME)
        data = response['Body'].read()
        return pd.read_parquet(BytesIO(data))
    except Exception as e:
        st.error(f"Error loading COI table: {e}")
        return pd.DataFrame()
    
def update_coi_df_on_submit(df, response, coi_table_container):
    if response.status_code == 200:
        st.write(response)
        # resp_json = response.json()
        # message = resp_json.get("message", "Success")
        placeholder = st.empty()
        # placeholder.success(message)
        # Clear the cached table so the next load reflects the update
        load_coi_table.clear()
        coi_df = load_coi_table()
        coi_table_container.dataframe(coi_df)
        st.rerun()
        sleep(4)
        placeholder.empty()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")

