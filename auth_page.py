import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import streamlit as st

redirect_uri = os.environ.get("REDIRECT_URI", "https://baxter.streamlit.app/")

def auth_flow():
    st.write("Baxter Internal Tools")
    auth_code = st.query_params.get("code")
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "patent_examination_tool.json",
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
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
        assert user_info.get("email"), "Email not found in infos"
        st.session_state["google_auth_code"] = auth_code
        st.session_state["user_info"] = user_info
        st.query_params["page"] = "tool"  # Updated line
    else:
        authorization_url, state = flow.authorization_url()
        button_html = f'<a href="{authorization_url}" target="_self"><button style="background-color: #4285F4; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Sign in with Google</button></a>'
        st.markdown(button_html, unsafe_allow_html=True)

def main():
    if "google_auth_code" not in st.session_state:
        auth_flow()

if __name__ == "__main__":
    main()