---
title: AgentFlow
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AgentFlow - AI-Powered Task Agent

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_AI-000000?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F61?style=for-the-badge)
![Sentence Transformers](https://img.shields.io/badge/Sentence_Transformers-4285F4?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

An autonomous AI agent that takes a task, breaks it down into steps, picks the right tools, and solves it — all on its own. Built with FastAPI, Groq AI (LLaMA 3.3 70B), ChromaDB for RAG, and SQLite.

## What It Does

Give the agent any task and watch it think through the problem step by step:

- Searches the web for real-time information
- Runs Python code to solve programming tasks
- Calculates math expressions
- Looks up facts on Wikipedia
- Searches through your uploaded documents using RAG
- Gets current date and time

The agent decides which tool to use at each step, analyzes the result, and keeps going until it has the final answer.

## Screenshots

### Hero
![Hero](screenshots/hero.png)

### Agent Steps
![Agent Steps](screenshots/agent_steps.png)

### RAG - Document Upload
![RAG Upload](screenshots/rag_upload.png)

### Task History
![History](screenshots/history.png)

## Tech Stack

- **Python + FastAPI** — Backend API with SSE streaming
- **Groq API (LLaMA 3.3 70B)** — AI brain for reasoning and decision making
- **ChromaDB + Sentence Transformers** — Vector database for RAG (document search)
- **SQLite** — Task history and step logging
- **DuckDuckGo Search** — Web search tool
- **Wikipedia API** — Knowledge lookup tool
- **HTML/CSS/JavaScript** — Frontend with real-time step rendering

## Agent Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the internet using DuckDuckGo |
| `run_python` | Execute Python code safely in a sandbox |
| `calculator` | Solve math expressions (supports sqrt, sin, cos, log, etc.) |
| `wiki_search` | Look up topics on Wikipedia |
| `get_datetime` | Get current date, time, and day |
| `search_documents` | Search uploaded documents using RAG with vector embeddings |

## How RAG Works

1. Upload any document (PDF, TXT, DOCX, etc.)
2. The text gets split into chunks and converted to vector embeddings
3. Embeddings are stored in ChromaDB (vector database)
4. When you ask a question, the agent uses `search_documents` to find the most relevant chunks
5. The AI answers based on the actual content from your documents

## Setup

### Prerequisites
- Python 3.10+
- Groq API key (free at https://console.groq.com)

### Installation

```bash
# clone the repo
git clone https://github.com/manojkumar-ra/agentflow.git
cd agentflow

# install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key
```

### Run

```bash
python main.py
```

Open `http://localhost:8001` in your browser.

## Deployment

This app is deployed on **Hugging Face Spaces** using Docker. The `Dockerfile` and HF config header at the top of this README handle the deployment automatically.

## Project Structure

```
agentflow/
├── main.py            # FastAPI server + API endpoints
├── agent.py           # AI agent loop (reasoning + tool selection)
├── tools.py           # All agent tools (search, python, calc, wiki, docs)
├── rag.py             # RAG module (ChromaDB + embeddings + document processing)
├── database.py        # SQLite database for task history
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker config for HF Spaces
├── .env               # API keys (not in repo)
├── static/
│   └── index.html     # Frontend UI
└── chroma_db/         # Vector database storage (auto-created)
```

## How the Agent Works

1. User gives a task
2. The AI reads the task and decides which tool to use first
3. Tool executes and returns a result
4. AI analyzes the result and decides the next step
5. Repeats until the AI has enough info to give a final answer
6. All steps are streamed to the frontend in real-time via SSE
7. Task and steps are saved to SQLite for history
