import base64
import os
import uuid
import requests
import streamlit as st

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # Strictly under 5 MB for POC
PARSER_OPTIONS = ["markitdown", "anydoc", "docling"]  # "markitdown" is index 0 (default)

st.set_page_config(page_title="Document to Markdown POC", layout="wide")
st.title("Document to Markdown Extraction POC")
st.caption("Upload a file under 5 MB. Default parser is MarkItDown; output is rendered as Markdown text.")

# API Gateway REST API endpoint (set via environment variable in deployment or local testing)
api_url = st.text_input(
    "API Gateway REST API Endpoint (/extract)",
    value=os.getenv("EXTRACT_API_URL", ""),
    placeholder="https://<api-id>.execute-api.ap-south-2.amazonaws.com/prod/extract",
)

selected_parser = st.radio(
    "Select Extraction Mode / Parser",
    options=PARSER_OPTIONS,
    index=0,  # Defaults to "markitdown"
    horizontal=True,
)

uploaded_file = st.file_uploader(
    "Upload a document (< 5 MB)",
    type=["pdf", "docx", "xlsx", "pptx", "txt", "md", "html"],
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_size = len(file_bytes)

    if file_size >= MAX_FILE_SIZE_BYTES:
        st.error(f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds the POC limit of 5 MB.")
        st.stop()

    doc_id = str(uuid.uuid4())
    st.subheader("Reference File Details")
    col1, col2, col3 = st.columns(3)
    col1.metric("Document ID", doc_id[:8] + "...")
    col2.metric("File Name", uploaded_file.name)
    col3.metric("File Size", f"{file_size / 1024:.1f} KB")

    if uploaded_file.type == "application/pdf":
        st.info(f"Reference PDF loaded: {uploaded_file.name} ({file_size} bytes)")
    elif uploaded_file.type and uploaded_file.type.startswith("text/"):
        with st.expander("Preview Reference Text"):
            st.text(file_bytes.decode("utf-8", errors="replace")[:3000])

    if st.button("Extract to Markdown", type="primary"):
        if not api_url.strip():
            st.warning("Please enter your API Gateway REST API endpoint URL first (or set EXTRACT_API_URL).")
            st.stop()

        payload = {
            "document_id": doc_id,
            "file_name": uploaded_file.name,
            "file_size": file_size,
            "parser": selected_parser or "markitdown",
            "file_base64": base64.b64encode(file_bytes).decode("utf-8"),
        }

        with st.spinner(f"Extracting using '{selected_parser}'..."):
            try:
                response = requests.post(api_url.strip(), json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                markdown_output = data.get("markdown", "")

                st.subheader("Extracted Markdown Output")
                st.markdown(markdown_output if markdown_output else "*No Markdown content returned.*")

                with st.expander("Raw Markdown Source"):
                    st.code(markdown_output, language="markdown")

                st.download_button(
                    label="Download .md",
                    data=markdown_output.encode("utf-8"),
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}.md",
                    mime="text/markdown",
                )
            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")