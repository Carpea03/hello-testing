import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import streamlit as st
import PyPDF2
import re
import requests
import json
import anthropic
from io import BytesIO

redirect_uri = os.environ.get("REDIRECT_URI", "https://hellotesting-y175lslw65h.streamlit.app/")

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
    else:
        authorization_url, state = flow.authorization_url()
        button_html = f'<a href="{authorization_url}" target="_self"><button style="background-color: #4285F4; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;">Sign in with Google</button></a>'
        st.markdown(button_html, unsafe_allow_html=True)

def extract_info(text):
    application_numbers = list(set(re.findall(r"Application number\s*:\s*(\d+)", text)))
    applicant_names = list(set(re.findall(r"Applicant name\w*\s*:\s*(.*)", text)))
    your_references = list(set(re.findall(r"Your reference\s*:\s*(\S.*)", text)))
    return application_numbers, applicant_names, your_references

def fetch_patent_details(application_number):
    api_key = "823956cf4bb3d1f4b7a883edc8ae10166c23a7da7db812c8f1722c89ec8a9d02"
    url = f"https://serpapi.com/search?engine=google_patents&q={application_number}&api_key={api_key}"
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def generate_output(input_text, patent_details, example_output_urls):
    client = anthropic.Anthropic()

    example_outputs = []
    for url in example_output_urls:
        response = requests.get(url)
        pdf_reader = PyPDF2.PdfReader(BytesIO(response.content))
        example_text = ""
        for page in pdf_reader.pages:
            example_text += page.extract_text()
        example_outputs.append(example_text)

    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        system="Act as an expert IP attorney working for Baxter IP Pty Ltd. Here are some example outputs to guide your response:\n\n{''.join(example_outputs)}",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Generate a letter to the client based on the following input and patent details:\n\nInput:\n{input_text}\n\nPatent Details:\n{json.dumps(patent_details, indent=2)}"
                    }
                ]
            }
        ]
    )

# Convert response.content to a string
    response_content_str = ''.join(item.text for item in response.content)

    # Format the response content with Markdown and preserve line breaks
    formatted_response = f"""
## Response Letter

{response_content_str}

""".format(response_content_str.replace('(', '\\(').replace(')', '\\)'))

    return formatted_response

def nav_to(url):
    nav_script = f"""
    <meta http-equiv="refresh" content="0; url='{url}'">
    """
    st.write(nav_script, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="LTC PP Exam Report", page_icon=":guardsman:", layout="wide", initial_sidebar_state="expanded")
    if "google_auth_code" not in st.session_state:
        auth_flow()
    if "google_auth_code" in st.session_state:
        email = st.session_state["user_info"].get("email")
        st.write(f"Hello {email}")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            with st.expander("Text Extraction"):
                application_numbers, applicant_names, your_references = extract_info(text)
                if application_numbers:
                    for i, application_number in enumerate(application_numbers):
                        st.write(f"Application Number {i+1}: {application_number}")
                        if i < len(applicant_names):
                            st.write(f"Applicant Name {i+1}: {applicant_names[i]}")
                        else:
                            st.write(f"Applicant Name {i+1}: Not found")
                        if i < len(your_references):
                            st.write(f"Your Reference {i+1}: {your_references[i]}")
                        else:
                            st.write(f"Your Reference {i+1}: Not found")
                else:
                    st.write("No application numbers found in the uploaded file.")
            
            with st.expander("Google Patents Lookup"):
                patent_details_list = []
                for application_number in application_numbers:
                    patent_details = fetch_patent_details(application_number)
                    patent_details_list.append(patent_details)
                    st.write(f"Patent Details for Application Number {application_number}:")
                    st.write(patent_details)
            
            example_output_urls = [
                "https://drive.google.com/uc?export=download&id=1KZ4bc5d_Lnugp5XBKoUC3U5HUh71dBJz",
                "https://drive.google.com/uc?export=download&id=1KYkrTkQ_Dvoa7jZAZluswQ_0Y8RiVI2G",
            ]
            
            output = generate_output(text, patent_details_list, example_output_urls)
            st.markdown(output, unsafe_allow_html=True)

if __name__ == "__main__":
    main()