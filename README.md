# AgentFlow - AI-Powered Task Agent

An autonomous AI agent that takes a task, breaks it down into steps, picks the right tools, and solves it — all on its own. Built with FastAPI, Groq AI (LLaMA 3.3 70B), ChromaDB for RAG, and MySQL.

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

_coming soon_

## Tech Stack

- **Python + FastAPI** — Backend API with SSE streaming
- **Groq API (LLaMA 3.3 70B)** — AI brain for reasoning and decision making
- **ChromaDB + Sentence Transformers** — Vector database for RAG (document search)
- **MySQL** — Task history and step logging
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
- MySQL
- Groq API key (free at https://console.groq.com)

### Installation

```bash
# clone the repo
git clone https://github.com/manojkumar-ra/agentflow.git
cd agentflow

# install dependencies
pip install -r requirements.txt

# create .env file
```

### Environment Variables

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=agentflow
```

### Run

```bash
python main.py
```

Open `http://localhost:8001` in your browser.

## Project Structure

```
agentflow/
├── main.py            # FastAPI server + API endpoints
├── agent.py           # AI agent loop (reasoning + tool selection)
├── tools.py           # All agent tools (search, python, calc, wiki, docs)
├── rag.py             # RAG module (ChromaDB + embeddings + document processing)
├── database.py        # MySQL database for task history
├── requirements.txt   # Python dependencies
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
7. Task and steps are saved to MySQL for history
