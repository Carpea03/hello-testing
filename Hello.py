import streamlit as st
import PyPDF2
import re
import requests
import json
import anthropic
from io import BytesIO

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
    
    patent_details = data.get("organic_results", [])
    if patent_details:
        patent_details = patent_details[0]
        abstract = patent_details.get("abstract", "")
        claims = patent_details.get("claims", [])
        cited_patents = patent_details.get("cited_patents", [])
        non_patent_citations = patent_details.get("non_patent_citations", [])
        family_members = patent_details.get("family_members", [])
        legal_events = patent_details.get("legal_events", [])
        
        patent_details["abstract"] = abstract
        patent_details["claims"] = claims
        patent_details["cited_patents"] = cited_patents
        patent_details["non_patent_citations"] = non_patent_citations
        patent_details["family_members"] = family_members
        patent_details["legal_events"] = legal_events
    
    return patent_details

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
        system=f"Act as an expert Australian patents attorney working for Baxter IP Pty Ltd. Remember that in Australia the 'final date for acceptance' is the date to which all issues that are raised by IP Australia must be resolved otherwise the application lapses. Here are some example outputs to guide your response:\n\n{''.join(example_outputs)}.",
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
## Draft LTC

{response_content_str}

""".format(response_content_str.replace('(', '\\(').replace(')', '\\)'))

    return formatted_response

def main():
    uploaded_file = st.file_uploader("Upload an LFO PP PDF", type="pdf")
    if uploaded_file is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        with st.expander("Text Extraction"):
            application_numbers, applicant_names, your_references = extract_info(text)
            st.write(f"Application numbers: {application_numbers}")  # Debug statement
            st.write(f"Applicant names: {applicant_names}")  # Debug statement
            st.write(f"Your references: {your_references}")  # Debug statement
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
                st.write(f"Fetching patent details for application number: {application_number}")  # Debug statement
                patent_details = fetch_patent_details(application_number)
                patent_details_list.append(patent_details)
                st.write(f"Patent Details for Application Number {application_number}:")
                st.write(patent_details)
        example_output_urls = [
            "https://drive.google.com/uc?export=download&id=1KZ4bc5d_Lnugp5XBKoUC3U5HUh71dBJz",
            "https://drive.google.com/uc?export=download&id=1KYkrTkQ_Dvoa7jZAZluswQ_0Y8RiVI2G",
        ]
        st.write("Generating output...")  # Debug statement
        output = generate_output(text, patent_details_list, example_output_urls)
        st.markdown(output, unsafe_allow_html=True)

if __name__ == "__main__":
    main()