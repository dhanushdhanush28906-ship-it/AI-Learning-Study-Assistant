from langchain_ollama import ChatOllama


def get_llm():

    llm = ChatOllama(
        model="qwen2.5:3b",
        temperature=0,
        num_predict=512
    )

    return llm