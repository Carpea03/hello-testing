import streamlit as st
import PyPDF2
import re
import requests
import json
import anthropic
from io import BytesIO
from serpapi import GoogleSearch

def extract_info(text):
    application_numbers = list(set(re.findall(r"Application number\s*:\s*(\d+)", text)))
    applicant_names = list(set(re.findall(r"Applicant name\w*\s*:\s*(.*)", text)))
    your_references = list(set(re.findall(r"Your reference\s*:\s*(\S.*)", text)))
    return application_numbers, applicant_names, your_references

def fetch_patent_details(application_numbers):
    params = {
        "engine": "google_patents_details",
        "patent_id": f"patent/AU{application_numbers}",
        "api_key": "823956cf4bb3d1f4b7a883edc8ae10166c23a7da7db812c8f1722c89ec8a9d02"
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    patent_details = {}
    patent_details["title"] = results.get("title", "")
    patent_details["abstract"] = results.get("abstract", "")
    patent_details["claims"] = results.get("claims", [])
    patent_details["description_link"] = results.get("description_link", "")
    
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
                        "text": f"When you reply, first plan how you should answer within <thinking></thinking> XML tags. This is a space for you to write down relevant content and will not be shown to the user.\n\nOnce you are done thinking, output your final answer to the user within <answer></answer> XML tags. Make sure the answer is detailed and specific.\n\nHere is the user question:\n<question>\nGenerate a letter to the client based on the following input and patent details:\n\nInput:\n{input_text}\n\nPatent Details:\n{json.dumps(patent_details, indent=2)}\n</question>"
                    }
                ]
            }
        ]
    )
    
    # Extract thinking and answer parts from the response
    response_content_str = ''.join(item.text for item in response.content)
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', response_content_str, re.DOTALL)
    answer_match = re.search(r'<answer>(.*?)</answer>', response_content_str, re.DOTALL)
    
    thinking = thinking_match.group(1).strip() if thinking_match else "No thinking found."
    answer = answer_match.group(1).strip() if answer_match else "No answer found."
    
    # Format the answer with Markdown and preserve line breaks
    formatted_answer = f"""
    ## Draft LTC
    {answer}
    """.format(answer.replace('(', '\\(').replace(')', '\\)'))
    
    return thinking, formatted_answer

def main():
    uploaded_file = st.file_uploader("Upload an LFO PP PDF", type="pdf")
    if uploaded_file is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        with st.expander("Text Extraction"):
            application_numbers, applicant_names, your_references = extract_info(text)
            st.write(f"Application numbers: {application_numbers}")
            st.write(f"Applicant names: {applicant_names}")
            st.write(f"Your references: {your_references}")
            
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
                st.write(f"Fetching patent details for application number: {application_number}")
                patent_details = fetch_patent_details(application_number)
                patent_details_list.append(patent_details)
                st.write(f"Patent Details for Application Number {application_number}:")
                st.write(patent_details)
        
        example_output_urls = [
 "https://drive.google.com/uc?export=download&id=1-2_RyafaxbTPk8puaedbL70Iveod05Bt",
 "https://drive.google.com/uc?export=download&id=11CE5tozpqSjBxeZBeLdJUgukIw1e43_g",
 "https://drive.google.com/uc?export=download&id=11na8qj0NOxNRmkb6eF7zNnlOnAWE2SXo",
 "https://drive.google.com/uc?export=download&id=15_GtrA02bIZcTrUxpZh6u-OPjAMfYCMd",
 "https://drive.google.com/uc?export=download&id=1BpozX46E5tMJStTg36H1j7SjPFRw69Jv",
 "https://drive.google.com/uc?export=download&id=1Kh6HV7fiR49v5WtWJS4nxcwel7f7ZFCm",
 "https://drive.google.com/uc?export=download&id=1LgyWezeiEwwEfx8rdWBK3_2mZmO231Ha",
 "https://drive.google.com/uc?export=download&id=1LhZwax4vHc_9qfMQ6jUqkHNZ0vgYVhe-",
 "https://drive.google.com/uc?export=download&id=1Nxavxm2tp2RJUBJrRVmn0GeOG9irxYgP",
 "https://drive.google.com/uc?export=download&id=1P-rvnczpMDruJRKzhA1kXzzTy13RGU1y",
 "https://drive.google.com/uc?export=download&id=1fneuEBn2xILWHSL4SAF67dMgMdVoCUUd",
 "https://drive.google.com/uc?export=download&id=1kEF4xiTgWAIdDnmC5Zkm3Vxm4OdWn0pA",
 "https://drive.google.com/uc?export=download&id=1kHkgam7cTE6J2L85wwcrJ-ZT0MiPoi8E",
 "https://drive.google.com/uc?export=download&id=1l4ifeydtdVfXuWqfxKPGv9KQ1ixI3DMW",
 "https://drive.google.com/uc?export=download&id=1n5rufXG0ysD5J1VUYvADNcreU4F2rESX",
 "https://drive.google.com/uc?export=download&id=1oOQMYU6gz4JBu59-AZUll6H67Z_A85lT",
 "https://drive.google.com/uc?export=download&id=1pVYbCGM3bhNpFTXInpMg0VR966H-fW5d",
 "https://drive.google.com/uc?export=download&id=1pf2XqTHAPFv-AGBTHALXh3Adeq7IJh0o",
 "https://drive.google.com/uc?export=download&id=1zsi5V38ixs6_UFMwJpHStmfvBPksD9OY"
]
        
    st.write("Generating output...")
    thinking, answer = generate_output(text, patent_details_list, example_output_urls)
    
    st.write("Thinking:")
    st.write(thinking)
    
    st.write("Answer:")
    st.markdown(answer, unsafe_allow_html=True)

if __name__ == "__main__":
    main()