import streamlit as st
import boto3
import requests
import time
from jose import jwt
from urllib.parse import urlencode

# Initialize the Cognito boto3 client once globally
cognito_client = boto3.client(
    'cognito-idp',
    region_name=st.secrets["cognitoClient"]["REGION"],
    aws_access_key_id=st.secrets["cognitoClient"]["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["cognitoClient"]["AWS_SECRET_ACCESS_KEY"],
)

# Secrets for your Cognito App
USER_POOL_ID = st.secrets["cognito"]["user_pool_id"]
CLIENT_ID = st.secrets["cognito"]["client_id"]
COGNITO_DOMAIN = st.secrets["cognito"]["domain"]  # if needed for future
REDIRECT_URI = st.secrets["cognito"]["redirect_uri"]  # if needed for future


def get_tokens_directly_admin_auth(email, password):
    """
    Authenticate user using AdminInitiateAuth and save tokens in session state.
    """

    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
            }
        )

        # Save tokens
        st.session_state.id_token = response['AuthenticationResult']['IdToken']
        st.session_state.access_token = response['AuthenticationResult']['AccessToken']
        st.session_state.refresh_token = response['AuthenticationResult']['RefreshToken']

        st.success("Authentication successful.")
        return True

    except cognito_client.exceptions.NotAuthorizedException:
        st.error("Incorrect username or password.")
        return False

    except cognito_client.exceptions.UserNotFoundException:
        st.error("User does not exist.")
        return False

    except Exception as e:
        st.error(f"Unexpected error during authentication: {e}")
        return False
    


def refresh_tokens_if_needed():
    """
    Refresh id_token and access_token automatically using the refresh_token.
    Silently refresh without bothering the user.
    """

    if "refresh_token" not in st.session_state or "id_token" not in st.session_state:
        return False  # No tokens available to refresh

    try:
        # Decode the id_token to check expiration
        decoded_token = jwt.get_unverified_claims(st.session_state.id_token)
        exp_timestamp = decoded_token["exp"]
        current_timestamp = int(time.time())

        # Refresh if token expires in next 5 minutes
        if exp_timestamp - current_timestamp < 300:
            # Perform silent token refresh
            response = cognito_client.admin_initiate_auth(
                UserPoolId=USER_POOL_ID,
                ClientId=CLIENT_ID,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': st.session_state.refresh_token
                }
            )

            # Update session_state with new tokens
            st.session_state.id_token = response['AuthenticationResult']['IdToken']
            st.session_state.access_token = response['AuthenticationResult']['AccessToken']

            return True

        return True  # Token still valid, no need to refresh

    except Exception as e:
        st.error(f"Failed to refresh session: {e}")
        return False

