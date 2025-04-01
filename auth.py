import streamlit as st
import sys
import os
import logging
import requests
import time
import json
from urllib.parse import urlencode
from jose import jwt, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError


# --- Load Cognito Config ---
try:
    COGNITO_DOMAIN = st.secrets["cognito"]["domain"]
    CLIENT_ID = st.secrets["cognito"]["client_id"]
    REDIRECT_URI = st.secrets["cognito"]["redirect_uri"]
    REGION = st.secrets["cognito"]["region"]
    USER_POOL_ID = st.secrets["cognito"]["user_pool_id"]
except (AttributeError, KeyError):
    logging.warning("Cognito secrets not found. Using hardcoded values (NOT FOR PRODUCTION).")
    COGNITO_DOMAIN = "https://<your-prefix>.auth.<region>.amazoncognito.com"
    CLIENT_ID = "<your-app-client-id>"
    REDIRECT_URI = "http://localhost:8501"
    REGION = "<your-aws-region>"
    USER_POOL_ID = "<your-user-pool-id>"

    if "<your-prefix>" in COGNITO_DOMAIN or "<your-app-client-id>" in CLIENT_ID:
        st.error("Please configure your Cognito settings in '.streamlit/secrets.toml' or replace placeholders.")
        st.stop()

# --- URLs ---
TOKEN_URL = f"{COGNITO_DOMAIN}/oauth2/token"
AUTHORIZATION_URL = f"{COGNITO_DOMAIN}/oauth2/authorize" # this includes new user sign up option
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
REDIRECT_URI_WITH_LOGOUT = "http://localhost:8501?logout=true"
LOGOUT_URL = f"{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={REDIRECT_URI_WITH_LOGOUT}"



ISSUER_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"

def handle_auth():
    """
    Call this function at the top of your app.py.
    It handles login, logout, token validation, and session state.
    Returns True if authenticated, False otherwise.
    """

    query_params = st.query_params

    if "logout" in query_params:
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()


    # --- Fetch and Cache Public Keys ---
    @st.cache_resource(ttl=10800)
    def get_public_keys():
        try:
            response = requests.get(JWKS_URL, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            return {key['kid']: jwk.construct(key) for key in jwks['keys']}
        except Exception as e:
            logging.error(f"Failed to fetch JWKS: {e}")
            st.error("Could not fetch Cognito public keys.")
            return {}

    PUBLIC_KEYS = get_public_keys()

    # --- Validate JWT ---
    def validate_token(token, access_token=None):
        if not PUBLIC_KEYS:
            return None

        try:
            headers = jwt.get_unverified_headers(token)
            kid = headers['kid']

            if kid not in PUBLIC_KEYS:
                st.error("Authentication failed: Unknown token signature key.")
                return None

            public_key = PUBLIC_KEYS[kid]
            payload = jwt.decode(
                token,
                public_key.to_pem(),
                algorithms=['RS256'],
                audience=CLIENT_ID,
                issuer=ISSUER_URL,
                access_token=access_token
            )

            if time.time() > payload['exp']:
                st.error("Authentication failed: Token expired.")
                return None

            if payload.get('token_use') != 'id':
                st.error("Authentication failed: Invalid token use.")
                return None

            return payload

        except ExpiredSignatureError:
            st.error("Authentication failed: Token expired.")
            return None
        except JWTClaimsError as e:
            st.error(f"Invalid token claims: {e}")
            return None
        except JWTError as e:
            st.error(f"JWT Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected token validation error: {e}")
            st.error("Authentication failed.")
            return None

    # --- Trigger rerun if needed ---
    if st.session_state.get('trigger_rerun'):
        st.session_state['trigger_rerun'] = False
        st.rerun()

    # --- Init Session ---
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.auth_code = None
        st.session_state.user_info = None
        st.session_state.id_token = None

    # --- Handle Authorization Code from Redirect ---
    query_params = st.query_params
    if not st.session_state.authenticated and "code" in query_params:
        st.session_state.auth_code = query_params["code"]
        st.query_params.clear()

    # --- Exchange Authorization Code for Tokens ---
    if not st.session_state.authenticated and st.session_state.auth_code:
        with st.spinner("Authenticating..."):
            try:
                token_request_data = {
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'code': st.session_state.auth_code,
                    'redirect_uri': REDIRECT_URI
                }
                response = requests.post(TOKEN_URL, data=token_request_data)
                response.raise_for_status()
                tokens = response.json()
                id_token = tokens.get('id_token')
                access_token = tokens.get('access_token')

                if not id_token:
                    st.error("Authentication failed: No ID Token.")
                    st.session_state.auth_code = None
                    st.button("Retry Login")
                else:
                    validated_payload = validate_token(id_token, access_token)
                    if validated_payload:
                        st.session_state.authenticated = True
                        st.session_state.user_info = validated_payload
                        st.session_state.id_token = id_token
                        st.session_state.auth_code = None
                        st.session_state['trigger_rerun'] = True
                    else:
                        st.session_state.auth_code = None
                        st.button("Retry Login")

            except requests.exceptions.RequestException as e:
                error_details = ""
                try:
                    error_details = e.response.json()
                except:
                    pass
                st.error(f"Token exchange failed. Details: {error_details}")
                st.session_state.auth_code = None
                if st.button("Retry Login"):
                    st.rerun()
                st.stop()
            except Exception as e:
                st.error("Unexpected error during authentication.")
                st.session_state.auth_code = None
                if st.button("Retry Login"):
                    st.rerun()
                st.stop()



    # --- Show Login Button ---
    if not st.session_state.authenticated:
        auth_params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': REDIRECT_URI
        }
        login_url = f"{AUTHORIZATION_URL}?{urlencode(auth_params)}"

        st.markdown(f"""
        ### Welcome!
        Please log in to continue.

        <a href="{login_url}" target="_self" style="display: inline-block; padding: 0.5em 1em; background-color: #FF9900; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
            Login with Cognito
        </a>
        """, unsafe_allow_html=True)
        st.stop()

    # --- Authenticated UI ---
    if st.session_state.authenticated:
        st.sidebar.header("User Info")
        user_info = st.session_state.user_info
        email = user_info.get('email', 'N/A')
        username = user_info.get('cognito:username', 'N/A')
        name = user_info.get('name', user_info.get('given_name', 'N/A'))

        st.sidebar.write(f"**Username:** {username}")
        st.sidebar.write(f"**Email:** {email}")
        st.sidebar.write(f"**Name:** {name}")
        st.sidebar.markdown(f'<a href="{LOGOUT_URL}" target="_self" style="display: inline-block; padding: 0.5em 1em; background-color: #DDDDDD; color: black; text-decoration: none; border-radius: 4px;">Logout</a>', unsafe_allow_html=True)


