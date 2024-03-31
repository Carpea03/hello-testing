import webbrowser
import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import streamlit as st

redirect_uri = os.environ.get("REDIRECT_URI", "https://baxter.streamlit.app")

def auth_flow():
    st.write("Baxter Internal Tools")
    auth_code = st.query_params.get("code")
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "patent_examination_tool.json",
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
        st.session_state["google_auth_code"] = auth_code
        st.session_state["user_info"] = user_info
    else:
        if st.button("Sign in with Google"):
            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
            )
            webbrowser.open_new_tab(authorization_url)

def main():
    if "google_auth_code" not in st.session_state:
        auth_flow()

    if "google_auth_code" in st.session_state:
        email = st.session_state["user_info"].get("email")
        st.write(f"Hello {email}")


if __name__ == "__main__":
    main()