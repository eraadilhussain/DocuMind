# DocuMind 🧠
**An Agentic RAG (Retrieval-Augmented Generation) Chat Application with Hybrid Retrieval.**

![DocuMind Preview](https://img.shields.io/badge/Status-Active-brightgreen) ![License](https://img.shields.io/badge/License-MIT-blue)

Built by **Er Aadil Hussain**.

DocuMind is an advanced full-stack AI chat application that allows users to upload documents (PDF, DOCX, TXT) and web URLs to create a dynamic, conversational knowledge base. It uses agentic intent routing to intelligently decide when to retrieve information from your documents versus when to answer general queries directly. 

---

## ✨ Key Features

### 🎨 Stunning UI / UX
- **Next.js & Tailwind CSS**: A blazing-fast frontend with a premium, glassmorphism design.
- **Collapsible Sidebar**: Beautifully animated sidebar to manage your chat history, auto-grouped by date (Today, Yesterday, Last 7 days, Older).
- **Dynamic Document Panel**: A dedicated interface to drag-and-drop files or paste web URLs. Auto-closes upon successful upload.
- **Streaming Responses**: Real-time token streaming for a ChatGPT-like experience.
- **Markdown & Code Support**: Beautifully renders markdown, tables, and syntax-highlighted code blocks.

### 🧠 Agentic Intelligence
- **Intent Routing**: The backend agent analyzes your prompt to route it to the optimal processing pipeline (e.g., direct LLM response vs. vector database search).
- **Auto-Titling**: Automatically generates a concise title for new chats based on your first message.
- **Hybrid Retrieval**: Combines dense vector search with traditional keyword search (BM25/sparse) via Qdrant to ensure highly accurate document retrieval.

### ⚙️ Robust Backend & Infrastructure
- **FastAPI**: High-performance asynchronous Python backend.
- **Qdrant Vector Database**: Local, persistent vector storage for lightning-fast semantic search.
- **SQLite & SQLAlchemy**: Relational storage for chats, messages, and document metadata.
- **Document Management**: Full CRUD support for documents, including surgical vector deletion from Qdrant when a document is removed.

---

## 🏗️ Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **State Management**: Zustand
- **Styling**: Tailwind CSS, Vanilla CSS (CSS Modules)
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python)
- **LLM Engine**: Groq API (High-speed OSS Models)
- **Vector Database**: Qdrant (Local Persistent)
- **Relational Database**: SQLite (via SQLAlchemy)
- **Document Processing**: LangChain, python-docx, pdfplumber, BeautifulSoup4

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.10+
- A Groq API Key

### 1. Clone the repository
```bash
git clone https://github.com/eraadilhussain/DocuMind.git
cd DocuMind
```

### 2. Set up the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file in the `backend/` folder:
```env
GROQ_API_KEY=your_groq_api_key_here
```
Start the backend server:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Set up the Frontend
Open a new terminal and navigate to the frontend:
```bash
cd frontend
npm install
```
Start the Next.js development server:
```bash
npm run dev
```

Visit `http://localhost:3000` in your browser to start using DocuMind!

---

## 🌍 Deployment

This project is fully configured to be deployed as a unified system on **Render**. 

The repository includes a `render.yaml` Blueprint which automatically provisions:
1. A Node.js web service for the Frontend.
2. A Python web service for the Backend.
3. A **1GB Persistent Disk** mounted at `/data` to ensure your SQLite database, uploaded files, and Qdrant vectors are permanently saved.

**To deploy:**
1. Push this repository to GitHub.
2. Log into [Render.com](https://render.com).
3. Click **New +** > **Blueprint**.
4. Select your repository and Render will handle the rest!

---

## 👨‍💻 Author

**Er Aadil Hussain**

---

*Powered by Next.js, FastAPI, Qdrant, and Groq.*
