import streamlit as st
import boto3

def get_tokens_directly_admin_auth(email, password):
    """
    Authenticates the user directly with Cognito using AdminInitiateAuth (Admin User Password Auth flow).
    Stores id_token and access_token in st.session_state.
    """

    # Set up Cognito boto3 client using st.secrets
    client = boto3.client(
        'cognito-idp',
        region_name=st.secrets["cognitoClient"]["REGION"],
        aws_access_key_id=st.secrets["cognitoClient"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["cognitoClient"]["AWS_SECRET_ACCESS_KEY"],
    )

    try:
        response = client.admin_initiate_auth(
            UserPoolId=st.secrets["cognito"]["user_pool_id"],
            ClientId=st.secrets["cognito"]["client_id"],
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
            }
        )

        # Save tokens into session_state
        st.session_state.id_token = response['AuthenticationResult']['IdToken']
        st.session_state.access_token = response['AuthenticationResult']['AccessToken']
        st.session_state.refresh_token = response['AuthenticationResult']['RefreshToken']

        st.success("Authentication successful.")
        return True

    except client.exceptions.NotAuthorizedException:
        st.error("Invalid username or password.")
        return False
    except client.exceptions.UserNotFoundException:
        st.error("User does not exist.")
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False
