# College Information Chatbot

## Abdul kalam College of Engineering and Technology

### Project Description

The College Information Chatbot is an AI-based question-answering system designed to provide students with information about college rules, attendance, examinations, regulations, syllabus and frequently asked questions.

The chatbot uses PDF documents as its knowledge source. Students can ask questions in natural language, and the system retrieves relevant information from the available college documents.

## Features

* Answer questions about college attendance rules
* Provide examination-related information
* Explain college regulations
* Provide syllabus-related information
* Answer frequently asked questions
* Search information from PDF documents
* AI-based question answering
* Simple and user-friendly web interface

## Technologies Used

* Python
* Flask
* LangChain
* Large Language Model (LLM)
* Vector Database
* PDF Document Loader
* HTML
* CSS
* JavaScript

## Project Structure

```text
college_chatbot/
│
├── app.py
├── database.py
├── README.md
├── requirements.txt
│
├── documents/
│   ├── attendance_rules.pdf
│   ├── college_regulations.pdf
│   ├── examination_rules.pdf
│   ├── faq.pdf
│   └── syllabus.pdf
│
├── templates/
│   ├── base.html
│   └── ...
│
└── static/
    ├── css/
    └── ...
```

## Documents

The `documents` folder contains the PDF files used as the knowledge base for the chatbot.

### 1. Attendance Rules

`attendance_rules.pdf`

Contains information about attendance requirements, leave, attendance recording and attendance shortage.

### 2. College Regulations

`college_regulations.pdf`

Contains general information about academic discipline, identity cards, campus conduct, mobile phones, anti-ragging and academic integrity.

### 3. Examination Rules

`examination_rules.pdf`

Contains information about examination eligibility, examination hall rules, permitted materials, electronic devices and examination malpractice.

### 4. FAQ

`faq.pdf`

Contains frequently asked questions related to attendance, examinations, certificates, library and college notices.

### 5. Syllabus

`syllabus.pdf`

Contains an academic syllabus overview including theory courses, laboratory courses, projects and assessment.

## Installation

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Project

After activating the virtual environment, run:

```bash
python app.py
```

The Flask application will start on the local server.

Open the URL shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

## How the Chatbot Works

```text
College PDF Documents
        ↓
PDF Document Loading
        ↓
Text Extraction
        ↓
Text Splitting
        ↓
Document Embeddings
        ↓
Vector Database
        ↓
User Question
        ↓
Relevant Information Retrieval
        ↓
AI/LLM
        ↓
Chatbot Answer
```

## Example Questions

Students can ask questions such as:

* What are the attendance requirements?
* What are the examination rules?
* What happens if attendance is insufficient?
* What are the college regulations?
* What materials are allowed in the examination hall?
* Where can I find syllabus information?
* How can I apply for leave?
* What are the frequently asked questions?

## Purpose

The main purpose of this project is to make college information easily accessible to students through an AI-powered chatbot.

## Note

The PDF documents included in this project are intended as project/reference documents. Students should verify current official rules, regulations and syllabus with the college and affiliating university.
