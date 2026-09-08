import os

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma


DOCUMENT_FOLDER = "college_knowledge_base"
VECTOR_DB_FOLDER = "vector_db"


def create_vector_database():

    print("Loading knowledge base documents...")

    loader = DirectoryLoader(
        DOCUMENT_FOLDER,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )

    documents = loader.load()

    if not documents:
        print("No text files found in college_knowledge_base folder.")
        return

    print(f"Loaded {len(documents)} documents.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Created {len(chunks)} text chunks.")

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_FOLDER
    )

    print("Vector database created successfully!")

    return vector_db


def load_vector_database():

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vector_db = Chroma(
        persist_directory=VECTOR_DB_FOLDER,
        embedding_function=embeddings
    )

    return vector_db