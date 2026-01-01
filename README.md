# Scalable Computer Use Agent

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)
![Anthropic](https://img.shields.io/badge/AI-Claude%203.5%20Sonnet-important?style=for-the-badge&logo=anthropic)

A production-ready, containerized backend solution for the **Anthropic Computer Use Agent**.

This project transforms the original experimental Streamlit interface into a scalable, high-performance **FastAPI** architecture, featuring WebSocket streaming, asynchronous SQLite persistence, and a fully isolated Linux desktop environment inside Docker.

---

## Demo

Watch the 5-minute demo video:  
https://www.youtube.com/watch?v=P5A--Im6Z7c

The video demonstrates:
- Real-time chat interaction  
- Tool execution workflow  
- The agent interacting with the virtual Linux desktop via screenshots and commands  

---

## Architecture

Designed with **Clean Architecture** principles to ensure extensibility, maintainability, and scalability.

```mermaid
graph TD
    User[User / Browser] <-->|WebSocket & HTTP| FastAPI[FastAPI Backend]
    User <-->|noVNC Port 6080| VNC[Virtual Desktop]
    
    subgraph Docker Container
        FastAPI <-->|Async CRUD| SQLite[(SQLite Database)]
        FastAPI <-->|Events| Agent[AI Agent Logic]
        
        Agent <-->|API Calls| Anthropic[Anthropic API]
        Agent <-->|Shell/Mouse Commands| Linux[Linux OS / Xvfb]
        
        Linux -->|Display :1| VNC
    end
