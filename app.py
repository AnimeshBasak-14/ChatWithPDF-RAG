## RAG Q&A Conversation With PDF Including Chat History
import streamlit as st
import os
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.vectorstores import FAISS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")

hf_token = st.secrets["HUGGINGFACE_TOKEN"]["token"]
os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token


# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

## Set up Streamlit UI
st.title("Conversational RAG With PDF Uploads and Chat History")
st.write("Upload PDFs and chat with their content")

# Input the Groq API Key
# api_key = st.text_input("Enter your Groq API key:", type="password")

groq_api_key = st.secrets["GROQ_API_KEY"]["key"]
os.environ["GROQ_API_TOKEN"] = groq_api_key


# Ensure API key is provided
if not groq_api_key:
    st.warning("Please enter the Groq API Key")
    st.stop()

# Initialize LLM
llm = ChatGroq(groq_api_key=groq_api_key, model_name="Gemma2-9b-It")

# Chat interface
session_id = st.text_input("Session ID", value="default_session")

# Statefully manage chat history
if "store" not in st.session_state:
    st.session_state.store = {}

uploaded_files = st.file_uploader("Choose a PDF file", type="pdf", accept_multiple_files=True)

if uploaded_files:
    documents = []
    
    for uploaded_file in uploaded_files:
        temp_pdf_path = f"./temp_{uploaded_file.name}"  # Unique filename
        with open(temp_pdf_path, "wb") as file:
            file.write(uploaded_file.getvalue())

        try:
            loader = PyPDFLoader(temp_pdf_path)
            docs = loader.load()
            documents.extend(docs)
        finally:
            os.remove(temp_pdf_path)  # Cleanup file after loading

    # Split and create embeddings for the documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    splits = text_splitter.split_documents(documents)

    # Use FAISS instead of ChromaDB for Streamlit Cloud compatibility
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever()

    # Define system prompt
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    # Define QA system prompt
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        "{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Create RAG pipeline
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def get_session_history(session: str) -> BaseChatMessageHistory:
        if session_id not in st.session_state.store:
            st.session_state.store[session_id] = ChatMessageHistory()
        return st.session_state.store[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    # User input for questions
    user_input = st.text_input("Your question:")
    if user_input:
        session_history = get_session_history(session_id)
        response = conversational_rag_chain.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        st.write("Assistant:", response["answer"])

