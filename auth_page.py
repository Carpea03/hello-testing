import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import streamlit as st

redirect_uri = os.environ.get("REDIRECT_URI", "baxter.streamlit.app")

def auth_flow():
    st.write("Baxter Internal Tools")
    auth_code = st.query_params().get("code")
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "/workspaces/hello-testing/My Project 620.json",
        scopes=["https://www.googleapis.com/auth/userinfo.email","https://www.googleapis.com/auth/userinfo.profile","openid"],
        redirect_uri=redirect_uri,
    )
    
    if auth_code:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        st.write("Login Done")
        
        user_info_service = build(
            serviceName="oauth2",
            version="v2",
            credentials=credentials,
        )
        user_info = user_info_service.userinfo().get().execute()
        
        if "email" not in user_info:
            st.error("Email not found in user info")
            return
        
        st.session_state["google_auth_code"] = auth_code
        st.session_state["user_info"] = user_info
        st.query_params(page="tool")
        st.experimental_rerun()
    else:
        authorization_url, _ = flow.authorization_url(prompt="consent")
        
        button_html = f'<a href="{authorization_url}" target="_self"><button style="background-color: #4285F4; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Sign in with Google</button></a>'
        st.markdown(button_html, unsafe_allow_html=True)

def main():
    if "google_auth_code" not in st.session_state:
        auth_flow()
    else:
        # Add your main application logic here
        st.write("Welcome, you are logged in!")

if __name__ == "__main__":
    main()