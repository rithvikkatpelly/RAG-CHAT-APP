"""Chat with your documents: a Streamlit front end for a ragfoundry pipeline."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from ragfoundry import RAGPipeline

load_dotenv()
UPLOADS = Path("uploads")
SUPPORTED = ["pdf", "docx", "txt", "md", "csv", "xlsx", "xls"]

st.set_page_config(page_title="Document Chat", page_icon="📄", layout="wide")


@st.cache_resource(show_spinner="Loading models...")
def get_pipeline() -> RAGPipeline:
    return RAGPipeline.from_yaml(os.environ.get("RAG_CONFIG", "rag.yaml"))


rag = get_pipeline()
if "chat" not in st.session_state:
    st.session_state.chat = rag.chat()
    st.session_state.messages = []  # [{"role", "content", "sources"}] for display

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Documents")

    if rag.config.llm.provider == "groq" and not os.environ.get("GROQ_API_KEY"):
        key = st.text_input("Groq API key", type="password", help="console.groq.com/keys")
        if not key:
            st.info("Enter your Groq API key to start.")
            st.stop()
        os.environ["GROQ_API_KEY"] = key

    with st.form("add", clear_on_submit=True):
        files = st.file_uploader("Upload files", type=SUPPORTED, accept_multiple_files=True)
        url = st.text_input("Or a web page URL")
        if st.form_submit_button("Add to knowledge base", type="primary") and (files or url):
            UPLOADS.mkdir(exist_ok=True)
            sources = [str(UPLOADS / f.name) for f in files or []]
            for file, path in zip(files or [], sources):
                Path(path).write_bytes(file.getbuffer())
            sources += [url] if url else []
            with st.spinner("Reading and indexing..."):
                report = rag.ingest(sources)
            st.success(f"Added {report.chunks_added} chunks ({report.chunks_unchanged} unchanged)")
            for failure in report.failures:
                st.error(f"{Path(failure.source).name}: {failure.error}")

    indexed = rag.sources()
    st.subheader(f"Indexed ({len(indexed)})")
    for source, chunks in indexed.items():
        name, remove = st.columns([5, 1])
        name.caption(f"{Path(source).name if '://' not in source else source} · {chunks} chunks")
        if remove.button("✕", key=source, help="Remove from the knowledge base"):
            rag.delete_source(source)
            if Path(source).parent == UPLOADS.resolve():
                Path(source).unlink(missing_ok=True)
            st.rerun()

    if st.button("New conversation", use_container_width=True):
        st.session_state.chat.reset()
        st.session_state.messages = []
        st.rerun()

# --------------------------------------------------------------------- chat
st.title("📄 Chat with your documents")


def show_sources(sources: list[dict]) -> None:
    if sources:
        with st.expander(f"Sources ({len(sources)})"):
            for number, doc in enumerate(sources, start=1):
                page = f", page {doc['page'] + 1}" if isinstance(doc.get("page"), int) else ""
                st.markdown(f"**[{number}] {doc['name']}{page}**")
                st.caption(doc["text"][:400])


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message.get("sources", []))

if not indexed:
    st.info("Add documents in the sidebar, then ask a question about them.")
elif question := st.chat_input("Ask a question about your documents"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = st.session_state.chat.ask(question)
        st.markdown(result.answer)
        sources = [
            {
                "name": Path(doc.metadata.get("source", "")).name or doc.metadata.get("source"),
                "page": doc.metadata.get("page"),
                "text": doc.page_content,
            }
            for doc in result.documents
        ]
        show_sources(sources)
    st.session_state.messages.append(
        {"role": "assistant", "content": result.answer, "sources": sources}
    )
