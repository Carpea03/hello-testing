import streamlit as st

def main():
    st.set_page_config(page_title="Patent App", page_icon=":guardsman:", layout="wide")
    st.title("Welcome to the Baxter IP Internal Tools")
    st.write("Select an option from the sidebar to get started.")

if __name__ == "__main__":
    main()