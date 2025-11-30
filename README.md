🤖 Energent.ai Backend Challenge: Scalable Computer Use Agent
This repository contains a robust, scalable, and containerized backend solution for the Anthropic Computer Use Agent, developed as part of the Energent.ai technical challenge.

The original experimental Streamlit interface has been completely replaced with a FastAPI backend, utilizing WebSockets for real-time streaming, SQLite (Async) for persistence, and Docker for a fully isolated Linux execution environment with VNC support.

🚀 Key Features
⚡ High-Performance Backend: Built with FastAPI and Uvicorn, utilizing asynchronous Python for high concurrency.

🔄 Real-Time Streaming: Full-duplex WebSocket communication for instant chat interactions and live agent feedback.

🧠 Advanced Agent Integration: Integrated Claude 3.5 Sonnet (20241022) with "Computer Use" capabilities, handling tool execution loops and error recovery.

🖥️ Live VNC Integration: Embedded noVNC client allowing users to view the agent's virtual desktop and interactions in real-time within the browser.

💾 Persistent Memory: Chat history and session management persisted using SQLAlchemy (Async) and SQLite.

🐳 Fully Containerized: A single Dockerfile orchestrates the Backend, Virtual Display (Xvfb), Window Manager (Fluxbox), and VNC Server.

🛡️ Robust Error Handling: Includes defensive coding against invalid session IDs, API timeouts, and platform-specific incompatibilities.

🛠️ Tech Stack
Language: Python 3.11

Framework: FastAPI

AI Model: Anthropic Claude 3.5 Sonnet

Database: SQLite + SQLAlchemy (Async/Await)

Protocol: WebSocket

Virtualization: Docker, Xvfb, x11vnc, noVNC, Fluxbox

Frontend: HTML5, TailwindCSS, JavaScript (Vanilla)

📂 Project Structure
The project follows Clean Architecture principles to ensure maintainability and scalability.

Plaintext

energent-backend-challenge/
├── backend/
│   ├── main.py          # Application entry point, WebSocket & CORS configuration
│   ├── agent.py         # Anthropic Agent Logic & Tool Execution Loop
│   ├── crud.py          # Database operations (Create, Read)
│   ├── models.py        # SQLAlchemy Database Models (Session, ChatMessage)
│   ├── schemas.py       # Pydantic Schemas for Data Validation
│   └── database.py      # Async Database Connection Setup
├── computer_use_demo/   # Anthropic's original tool definitions (Refactored)
├── frontend/            # Single Page Application (Chat + VNC)
│   └── index.html
├── Dockerfile           # Multi-stage build for Linux environment & App
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (API Keys, Config)
⚡ Getting Started (Docker)
The easiest way to run the application is using Docker. It handles all system dependencies (xdotool, xvfb, etc.) automatically.

Prerequisites
Docker Desktop installed and running.

An Anthropic API Key with access to claude-3-5-sonnet-20241022.

1. Clone the Repository
Bash

git clone https://github.com/emrekurum/energent-backend-challenge.git
cd energent-backend-challenge
2. Configure Environment
Create a .env file in the root directory:

Bash

ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
WIDTH=1024
HEIGHT=768
DISPLAY_NUM=1
3. Build & Run
Build the Docker image (this may take a few minutes as it installs the Linux desktop environment):

Bash

docker build -t energent-agent .
Run the container (Mapping ports 8000 for API and 6080 for VNC):

Bash

docker run -p 8000:8000 -p 6080:6080 --env-file .env energent-agent
4. Access the Application
Open your browser and navigate to: 👉 http://127.0.0.1:8000

Chat: Interact with the agent on the right panel.

View: Watch the live Linux desktop on the left panel.

🧪 Usage Examples
Once the system is online, try these commands:

Basic Chat: "Hello, who are you?"

Computer Control: "Take a screenshot of the desktop." (You will see the screenshot appear in the chat).

Application Launch: "Open Firefox and check the https://www.google.com/search?q=google.com" (Watch the VNC screen on the left!).

🏗️ Design Decisions
Why FastAPI & WebSockets?
Unlike Streamlit (which is synchronous and reruns scripts), FastAPI provides a persistent, asynchronous server environment. WebSockets were chosen over HTTP polling to minimize latency for real-time tool outputs (like screenshots or cursor movements).

Why SQLite?
For this challenge, SQLite (via aiosqlite) was chosen for its zero-configuration setup and portability. However, the use of SQLAlchemy ORM allows for an instant switch to PostgreSQL in a production environment by simply changing the connection string.

Why Docker with Fluxbox?
The "Computer Use" agent requires a display server ($DISPLAY). Windows/Mac cannot natively provide the X11 interface required by tools like xdotool.

Xvfb: Creates a virtual frame buffer (headless display).

Fluxbox: A lightweight window manager to render windows (like Firefox) so the screenshots aren't just black boxes.

x11vnc + noVNC: Bridges the Docker display to the web browser via WebSocket.

🤝 Collaborators
Emre Kurum (Lead Developer)

Invited: lingjiekong, ghamry03, goldmermaid, EnergentAI

⚖️ License
Based on Anthropic Computer Use Demo. Modified for Energent.ai Challenge.