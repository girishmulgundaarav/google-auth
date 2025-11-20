import os
import time
import json
import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import jwt
from urllib.parse import urlencode
from dotenv import load_dotenv

# --- Load secrets ---
load_dotenv()  # Local dev; ignored in Streamlit Cloud
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", st.secrets.get("GOOGLE_CLIENT_ID", ""))
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", st.secrets.get("GOOGLE_CLIENT_SECRET", ""))
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", st.secrets.get("OAUTH_REDIRECT_URI", "http://localhost:8501/auth/callback"))
SCOPES = os.getenv("OAUTH_SCOPES", st.secrets.get("OAUTH_SCOPES", "openid email profile"))

# --- Google endpoints (OIDC discovery) ---
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISS = "https://accounts.google.com"

# --- Helpers ---
def get_oauth_session():
    return OAuth2Session(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope=SCOPES.split(),
        redirect_uri=REDIRECT_URI,
    )

def build_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

def verify_id_token(id_token: str) -> dict:
    # Fetch Google JWKS and validate the JWT
    import requests
    jwks = requests.get(GOOGLE_JWKS_URL, timeout=10).json()
    claims = jwt.decode(id_token, jwks)
    claims.validate(
        iss=GOOGLE_ISS,
        aud=CLIENT_ID,
        exp=int(time.time()) + 60  # strict validation; exp is already enforced internally
    )
    return claims

def logout():
    for k in ("user", "id_token", "access_token"):
        st.session_state.pop(k, None)
    st.success("Logged out.")

# --- UI ---
st.set_page_config(page_title="Google Auth with Streamlit", page_icon="🔐")

st.title("🔐 Google Auth Platform + Streamlit")

# Session initialization
if "user" not in st.session_state:
    st.session_state["user"] = None

# Router: detect callback route
# New (correct)
query_params = st.query_params  # returns a dict-like object
current_path = query_params.get("path", [""])[0] if "path" in query_params else ""
is_callback = "code" in query_params

# Login button
if st.session_state["user"] is None and not is_callback:
    st.info("You’re not signed in.")
    if st.button("Sign in with Google"):
        st.query_params.clear() # clear
        st.markdown(f'<meta http-equiv="refresh" content="0; url={build_auth_url()}">', unsafe_allow_html=True)

# Handle callback
if is_callback and st.session_state["user"] is None:
    code = st.request.query_params["code"]
    oauth = get_oauth_session()
    token = oauth.fetch_token(
        GOOGLE_TOKEN_URL,
        code=code,
        grant_type="authorization_code",
    )
    id_token = token.get("id_token")
    claims = verify_id_token(id_token)

    # Extract user info
    user = {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "email_verified": claims.get("email_verified", False),
        "name": claims.get("name"),
        "picture": claims.get("picture"),
        "given_name": claims.get("given_name"),
        "family_name": claims.get("family_name"),
    }
    st.session_state["user"] = user
    st.session_state["id_token"] = id_token
    st.session_state["access_token"] = token.get("access_token")

    # Clean URL after login
    st.query_params.clear()
    st.success(f"Signed in as {user.get('email')}")

# Authenticated content
if st.session_state["user"]:
    user = st.session_state["user"]
    cols = st.columns([1, 3])
    with cols[0]:
        if user.get("picture"):
            st.image(user["picture"], width=80)
    with cols[1]:
        st.markdown(f"**Signed in:** {user.get('name') or user.get('email')}")
        st.caption(f"Email: {user.get('email')} • Verified: {user.get('email_verified')}")

    st.divider()
    st.subheader("Protected app section")
    st.write("Only visible to authenticated users.")
    st.json(user)

    if st.button("Log out"):
        logout()