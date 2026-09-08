import os
import streamlit as st

from models import get_llm
from rag import create_vector_database, load_vector_database
from tools import get_current_date, college_contact_information, help_information


st.set_page_config(
    page_title="AI Student Support Assistant",
    page_icon="🎓",
    layout="wide"
)


# -----------------------------
# PAGE TITLE
# -----------------------------

st.title("🎓 AI Student Support Assistant")

st.write(
    "Ask questions about college regulations, syllabus, "
    "attendance, examinations and other student information."
)


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.header("⚙️ Controls")

    if st.button("📚 Create Knowledge Base"):

        with st.spinner("Creating vector database..."):

            create_vector_database()

        st.success("Knowledge Base Created Successfully!")


    if st.button("🗑 Clear Chat"):

        st.session_state.messages = []

        st.rerun()


    st.divider()

    st.subheader("Available Support")

    st.write("""
    - College Regulations
    - Attendance
    - Examinations
    - Course Syllabus
    - FAQs
    """)


# -----------------------------
# INITIALIZE MEMORY
# -----------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []


# -----------------------------
# DISPLAY OLD MESSAGES
# -----------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# -----------------------------
# USER QUESTION
# -----------------------------

question = st.chat_input("Ask your question here...")


if question:

    # Store user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message("user"):

        st.markdown(question)


    # -----------------------------
    # AI RESPONSE
    # -----------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            question_lower = question.lower()


            # -----------------------------
            # TOOL: HELP
            # -----------------------------

            if "help" in question_lower:

                answer = help_information()


            # -----------------------------
            # TOOL: DATE
            # -----------------------------

            elif "date" in question_lower or "today" in question_lower:

                answer = f"Today's date is {get_current_date()}"


            # -----------------------------
            # TOOL: CONTACT
            # -----------------------------

            elif "contact" in question_lower:

                answer = college_contact_information()


            # -----------------------------
            # RAG
            # -----------------------------

            else:

                if not os.path.exists("vector_db"):

                    answer = """
                    Knowledge Base is not created yet.

                    Please click:

                    Create Knowledge Base

                    in the sidebar first.
                    """

                else:

                    vector_db = load_vector_database()


                    # Search relevant documents

                    retrieved_documents = vector_db.similarity_search(
                        question,
                        k=4
                    )


                    # Combine retrieved information

                    context = "\n\n".join(

                        [
                            document.page_content

                            for document in retrieved_documents
                        ]

                    )


                    # -----------------------------
                    # MEMORY
                    # -----------------------------

                    chat_history = ""


                    recent_messages = st.session_state.messages[-6:]


                    for message in recent_messages:

                        chat_history += (
                            f"{message['role']}: "
                            f"{message['content']}\n"
                        )


                    # -----------------------------
                    # PROMPT
                    # -----------------------------

                    prompt = f"""
You are an AI Student Support Assistant.

Your role is to help college students.

Use the provided college information to answer questions.

If the answer is not available in the provided context,
clearly say that the information is not available
in the college documents.

Do not make up information.

Conversation History:

{chat_history}


College Document Context:

{context}


Student Question:

{question}


Give a clear and helpful answer.
"""


                    llm = get_llm()


                    response = llm.invoke(prompt)


                    answer = response.content


        st.markdown(answer)


    # Store assistant response

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )