
import streamlit as st
import requests
import time
import os

# Configuration
API_URL = "http://127.0.0.1:4567"
UPLOAD_ENDPOINT = f"{API_URL}/upload"
PROCESS_ENDPOINT = f"{API_URL}/process"
STATUS_ENDPOINT = f"{API_URL}/status"
DOWNLOAD_ENDPOINT = f"{API_URL}/download"

# Initialize session state
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'status' not in st.session_state:
    st.session_state.status = ""
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'total' not in st.session_state:
    st.session_state.total = 1

st.title("DAISY Book Generator")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    if st.session_state.file_path is None:
        with st.spinner('Uploading file...'):
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(UPLOAD_ENDPOINT, files=files)
                if response.status_code == 200:
                    st.session_state.file_path = response.json().get("file_path")
                    st.success(f"File uploaded successfully: {os.path.basename(st.session_state.file_path)}")
                else:
                    st.error(f"Error uploading file: {response.text}")
            except requests.exceptions.ConnectionError as e:
                st.error(f"Connection Error: Could not connect to the server at {API_URL}. Please ensure the server is running.")


# --- 2. Book Metadata and Processing ---
if st.session_state.file_path:
    st.header("Book Details")
    book_title = st.text_input("Title", "Sample Book Title")
    book_author = st.text_input("Author", "Sample Author")
    book_publisher = st.text_input("Publisher", "Sample Publisher")
    book_date = st.text_input("Publication Date (MM/DD/YYYY)", "01/01/2024")
    book_uid = st.text_input("UID", "uid-12345")
    chunk_size = st.slider("Chunk size", min_value=0, max_value=1000, value=400, step=1,)

    if st.button("Start DAISY Creation", disabled=(st.session_state.job_id is not None)):
        with st.spinner("Initializing process..."):
            payload = {
                "input_file": st.session_state.file_path,
                "book_title": book_title,
                "book_author": book_author,
                "book_publisher": book_publisher,
                "book_date": book_date,
                "book_uid": book_uid,
                "chunk_size": chunk_size
            }
            try:
                response = requests.post(PROCESS_ENDPOINT, json=payload)
                if response.status_code == 200:
                    st.session_state.job_id = response.json().get("job_id")
                    st.session_state.processing_complete = False
                    st.info(f"Processing started with Job ID: {st.session_state.job_id}")
                else:
                    st.error(f"Error starting process: {response.text}")
            except requests.exceptions.ConnectionError as e:
                st.error(f"Connection Error: Could not connect to the server at {API_URL}. Please ensure the server is running.")


# --- 3. Progress and Status ---
if st.session_state.job_id and not st.session_state.processing_complete:
    st.header("Processing Status")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while not st.session_state.processing_complete:
        try:
            status_response = requests.get(f"{STATUS_ENDPOINT}/{st.session_state.job_id}")
            if status_response.status_code == 200:
                data = status_response.json()
                st.session_state.status = data.get("status", "Unknown status...")
                st.session_state.progress = data.get("progress", 0)
                st.session_state.total = data.get("total", 1)

                # Update UI
                progress_value = st.session_state.progress / st.session_state.total if st.session_state.total > 0 else 0
                progress_bar.progress(progress_value)
                status_text.text(f"Status: {st.session_state.status}")

                if "finished" in st.session_state.status.lower():
                    st.session_state.processing_complete = True
                    st.success("Processing complete!")
                elif "error" in st.session_state.status.lower():
                    st.error(f"An error occurred: {st.session_state.status}")
                    break # Exit loop on error
            else:
                status_text.text("Waiting for server response...")

            time.sleep(2) # Poll every 2 seconds
        except requests.exceptions.ConnectionError as e:
            st.error(f"Connection Error: Could not get status from the server. Halting updates.")
            break
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            break


# --- 4. Download ---
if st.session_state.processing_complete:
    st.header("Download Result")
    st.info("Your DAISY book is ready for download.")
    
    # The download button in Streamlit works by providing a link with the data.
    # A direct link to the FastAPI endpoint is the cleanest way.
    download_url = f"{DOWNLOAD_ENDPOINT}/{st.session_state.job_id}"
    st.markdown(f'<a href="{download_url}" download><button>Download DAISY Book (.zip)</button></a>', unsafe_allow_html=True)

