import streamlit as st
from auth_page import main as auth_main
from LTC_PP import main as tool_main

def main():
    page = st.query_params.().get("page", ["auth"])[0]

    if page == "auth":
        auth_main()
    elif page == "tool":
        tool_main()

if __name__ == "__main__":
    main()