# admin_functions.py

import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import boto3
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

def add_new_coi(full_name, email, initial_tokens, initial_price, access_on, is_onboarded):
    """
    Adds a new COI to the database via API Gateway.
    """

    api_url = "https://xuyzj7f0zd.execute-api.us-east-1.amazonaws.com/prod/add-coi"
    data = {
        "email": email,
        "full_name": full_name,
        "token_balance": initial_tokens,
        "token_price": initial_price,
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


@st.cache_data(show_spinner="Loading COI Table...")
def load_coi_table(count=None):
    """
    Loads the COI table from S3 and returns it as a DataFrame.
    """

    try:
        response = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=COI_TABLE_NAME)
        data = response['Body'].read()
        df = pd.read_parquet(BytesIO(data))
        
        if count is not None:
            return df.head(count)
        
        return df

    except Exception as e:
        st.error(f"Error loading COI table: {e}")
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
