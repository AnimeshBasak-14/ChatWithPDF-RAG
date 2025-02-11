
# RAG Q&A Conversation With PDF Including Chat History

![Project Logo](img/project.png)

This project integrates **Streamlit**, **Groq**, and **Langchain** to provide a Conversational Retrieval-Augmented Generation (RAG) system. Users can upload PDF documents, and the system allows interaction with the content by asking questions, all while maintaining chat history for context-aware responses.

## Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.7 or higher
- `pip` (Python package installer)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/AnimeshBasak-14/rag-qa-chat-with-pdf-and-history.git
   cd rag-qa-chat-with-pdf-and-history
   ```
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Groq API key and HuggingFace token:

   ```
   HF_TOKEN=<your_huggingface_token>
   ```

   Replace `<your_huggingface_token>` with your HuggingFace API key.

## Running the Application

To run the chatbot app, use the following command:

```bash
streamlit run app.py
```

## To enable chat history and session state:

Uncomment these lines in app.py file to display the chat history and session data:

```
st.write(st.session_state.store)
st.write("Chat History:", session_history.messages)
```
