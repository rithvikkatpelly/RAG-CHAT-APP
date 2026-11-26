# Document Chat

A complete RAG app in about 145 lines (a 115-line `streamlit_app.py` plus a 35-line config file): upload documents, then chat with them. Built with
[ragfoundry](https://pypi.org/project/ragfoundry/) and Streamlit.

- Upload PDF, Word, TXT, Markdown, CSV or Excel files, or add a web page
- Ask questions and get answers with numbered citations and the passages they came from
- Follow-up questions work ("and how often?"), because the conversation is remembered
- Hybrid keyword + vector search, with a token budget on what is sent to the LLM
- Remove documents, or start a new conversation, from the sidebar
- Re-uploading a file only re-indexes the parts that changed
- Runs on Groq's `openai/gpt-oss-120b` by default, with local embeddings (no extra key needed)

## Project layout

| File | Purpose |
|---|---|
| `streamlit_app.py` | The Streamlit interface (the main file for Streamlit Cloud) |
| `rag.yaml` | The whole RAG pipeline: embeddings, vector store, LLM, chunking, retrieval |
| `requirements.txt` | Dependencies |
| `.streamlit/config.toml` | Streamlit settings: 200 MB upload limit and theme colour |
| `.streamlit/secrets.toml.example` | Template for your API key and settings |
| `sample_docs/` | Small documents to try it with |
| `storage/`, `uploads/` | Created on first run: the index and uploaded files |

## Run it

1. Install (Python 3.10 or newer):

   ```bash
   cd rag-chat-app
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   With [uv](https://docs.astral.sh/uv/) instead: `uv venv && uv pip install -r requirements.txt`.

2. Get a free Groq API key at https://console.groq.com/keys and put it in
   `.streamlit/secrets.toml`:

   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit GROQ_API_KEY
   ```

   Or skip this step and paste the key into the sidebar when the app opens.
   `.streamlit/secrets.toml` is in `.gitignore`, so your key is never committed.

3. Start the app:

   ```bash
   streamlit run streamlit_app.py
   ```

   It opens at http://localhost:8501. The first start downloads the embedding model (about
   90 MB), which takes a minute.

4. Upload files from `sample_docs/` (or your own), click **Add to knowledge base**, and ask
   something like "What does a sourdough starter need?" followed by "How often?".

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (without `.streamlit/secrets.toml`).
2. At https://share.streamlit.io, click **Create app**, pick the repo and branch, and set the
   main file path to `streamlit_app.py`.
3. Under **Advanced settings > Secrets**, paste:

   ```toml
   GROQ_API_KEY = "gsk_..."
   ```

4. Deploy. The first start installs dependencies and downloads the embedding model, so it takes
   a few minutes.

The cloud file system is temporary: indexed documents in `storage/` and `uploads/` are lost
whenever the app restarts or goes to sleep, so users need to upload their files again. For an
index that survives restarts, point `vector_store` in `rag.yaml` at a hosted store.

## Settings

Set these in `.streamlit/secrets.toml` (locally) or the app's Secrets box (on Streamlit Cloud).
Environment variables with the same names also work and take priority.

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | none | Groq API key. If missing, the app asks for it in the sidebar |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq model used to answer questions |
| `RAG_CONFIG` | `rag.yaml` | Pipeline config file to load |

## Customise

Everything about the pipeline is in `rag.yaml`; restart the app after changing it.

- **Different Groq model:** set `GROQ_MODEL` in your secrets (for example
  `GROQ_MODEL = "llama-3.3-70b-versatile"`), choosing from https://console.groq.com/docs/models.
- **Fully local, no API key:** install Ollama, run `ollama pull llama3.2`, and change the `llm`
  section to:

  ```yaml
  llm:
    provider: ollama
    model: llama3.2
  ```

- **OpenAI, Gemini or Claude:** set `llm.provider` to `openai`, `gemini` or `claude` with a model
  name, install the matching extra (for example `pip install "ragfoundry[openai]"`) and add its
  key to your secrets (`OPENAI_API_KEY`, `GOOGLE_API_KEY` or `ANTHROPIC_API_KEY`). The sidebar key field is only
  shown for Groq.
- **Better retrieval:** add a reranker under `retrieval`:

  ```yaml
  rerank:
    provider: huggingface
    model: cross-encoder/ms-marco-MiniLM-L-6-v2
  ```

- **Another vector store** (Qdrant, PGVector, Pinecone and more): see the
  [ragfoundry vector store guide](https://github.com/rithvikkatpelly/ragfoundry#8-vector-stores).
- **Several configs:** `RAG_CONFIG=other.yaml streamlit run streamlit_app.py`.

If you change the embedding model, also change `vector_store.collection_name` (or delete
`storage/`), because one index can't mix two embedding models.

## Reset everything

Stop the app and delete `storage/` and `uploads/`.
