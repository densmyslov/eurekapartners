# admin_functions.py

import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import boto3
from PIL import Image
import base64
import auth  # Import auth.py to refresh tokens

# --- Initialize S3 client ---
S3_CLIENT = boto3.client(
    's3',
    aws_access_key_id=st.secrets["s3"]["S3_ACCESS_KEY"],
    aws_secret_access_key=st.secrets["s3"]["S3_SECRET_KEY"]
)

# --- S3 constants ---
BUCKET_NAME = st.secrets["s3"]["BUCKET_NAME"]
COI_TABLE_NAME = st.secrets["s3"]["COI_TABLE_NAME"]
TRANSACTIONS_TABLE_NAME = st.secrets["s3"]["TRANSACTIONS_TABLE_NAME"]
DEFAULT_TOKEN_PRICES_DF_NAME = st.secrets["s3"]["DEFAULT_TOKEN_PRICES_DF_NAME"]
DEFAULT_BANKS_DF_NAME = st.secrets["s3"]["DEFAULT_BANKS_DF_NAME"]

# ==============================
#  HELPER FUNCTIONS
# ==============================

def safe_api_post(url, data):
    """
    Automatically refresh tokens if needed before sending an authorized POST request.
    """
    auth.refresh_tokens_if_needed()

    cognito_jwt_token = st.session_state.get("id_token")
    headers = {
        "Authorization": f"Bearer {cognito_jwt_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)
    
    # Optionally handle Unauthorized 401 error here and retry once (advanced)
    if response.status_code == 401:
        # Try refreshing token once more and retry request
        auth.refresh_tokens_if_needed()
        cognito_jwt_token = st.session_state.get("id_token")
        headers["Authorization"] = f"Bearer {cognito_jwt_token}"
        response = requests.post(url, json=data, headers=headers)

    return response


# ==============================
#  MAIN FUNCTIONS
# ==============================

def add_new_coi(first_name, last_name, email, initial_token_balance, price_qty_data, access_on, is_onboarded):
    """
    Adds a new COI to the database via API Gateway.
    """

    api_url = "https://xuyzj7f0zd.execute-api.us-east-1.amazonaws.com/prod/add-coi"
    data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "initial_token_balance": initial_token_balance,
        "price_qty_data": price_qty_data,
        "access_on": access_on,
        "is_onboarded": is_onboarded
    }
    return safe_api_post(api_url, data)


def delete_coi(emails):
    """
    Deletes COIs by sending a newline-separated string of emails.
    """

    api_url = "https://7893kaawd5.execute-api.us-east-1.amazonaws.com/prod/delete-coi"
    
    # emails is a list of emails -> join into a single string
    email_string = "\n".join(emails)

    data = {
        "emails": email_string  # <-- send a multi-line string
    }

    return safe_api_post(api_url, data)

def increment_counter():
    st.session_state.counter += 1

@st.cache_data(show_spinner="Loading COI Table...")
def load_coi_table(counter=None):
    """
    Loads the COI table from S3 and returns it as a DataFrame.
    """

    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=COI_TABLE_NAME)
        data = response['Body'].read()
        return pd.read_parquet(BytesIO(data))

    except Exception as e:
        st.error(f"Error loading COI table: {e}")
        st.write(COI_TABLE_NAME)
        return pd.DataFrame()  # Return empty DataFrame on error

@st.cache_data(show_spinner="Loading default price Table...")
def load_default_price_data(counter=None):
    """
    Loads the default price table from S3 and returns it as a DataFrame.
    """
    key = DEFAULT_TOKEN_PRICES_DF_NAME
    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=key)
        data = response['Body'].read()
        price_qty_df = pd.read_parquet(BytesIO(data))
        return price_qty_df.to_dict(orient='records')
    
    except Exception as e:
        st.error(f"Error loading default price table: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

@st.cache_data()   
def load_logo():
    image = Image.open("assets/eureka_logo.jpeg")
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return  base64.b64encode(buffered.getvalue()).decode()
    
@st.cache_data()
def load_transactions_df(counter=None):
    """
    Loads the transactions table from S3 and returns it as a DataFrame.
    """
    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=TRANSACTIONS_TABLE_NAME)
        data = response['Body'].read()
        return pd.read_parquet(BytesIO(data))

    except Exception as e:
        st.error(f"Error loading COI table: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

@st.cache_data()   
def load_default_banks_df(counter=None):
    """
    Loads the default banks table from S3 and returns it as a DataFrame.
    """
    key = DEFAULT_BANKS_DF_NAME
    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=key)
        data = response['Body'].read()
        return pd.read_parquet(BytesIO(data))
    
    except Exception as e:
        st.error(f"Error loading default banks table: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    

    


def update_coi_df_on_submit(df, response, coi_table_container):
    """
    After a successful add/delete API call:
    - Clears the cache
    - Reloads the updated COI table
    - Updates the UI container with the new table
    """

    if response.status_code == 200:
        placeholder = st.empty()

        # Clear cached load_coi_table
        load_coi_table.clear()

        # Reload fresh data
        fresh_df = load_coi_table()
        st.session_state.coi_df = fresh_df.copy()

        coi_table_container.dataframe(fresh_df)

        st.success("Operation successful!")

        placeholder.empty()

    else:
        st.error(f"Error: {response.status_code} - {response.text}")

def reload(coi_df=False, trans_df = False):
    increment_counter()
    if coi_df:
        load_coi_table.clear()
        st.session_state.coi_df = load_coi_table(counter=st.session_state.counter)
    if trans_df:
        trans_df = load_transactions_df(counter=st.session_state.counter)
    st.rerun()