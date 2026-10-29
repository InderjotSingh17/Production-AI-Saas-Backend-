# Production AI SaaS Backend

A production-oriented AI SaaS backend built with **FastAPI, Gemini, PostgreSQL/SQLAlchemy, Redis, and Celery**. The project focuses on secure API access, AI response generation, caching, rate limiting, background processing, streaming, and observability.

## 🚀 Features

- **Authentication** — JWT-based authentication and password hashing.
- **AI Integration** — Generate AI responses using Google's Gemini API.
- **Conversation Management** — Store conversations and messages in a database.
- **Streaming Responses** — Stream AI-generated content using Server-Sent Events (SSE).
- **Redis Caching** — Cache repeated prompts to reduce latency and unnecessary AI API calls.
- **Rate Limiting** — Enforce per-user request limits using Redis and atomic Lua operations.
- **AI Usage Tracking** — Track daily AI token usage.
- **Background Jobs** — Process asynchronous tasks using Celery workers.
- **Retry Handling** — Retry eligible background tasks with exponential backoff.
- **Observability** — Structured JSON logs, request IDs, request duration, and AI request metrics.
- **Docker Support** — Containerize the API and worker with Docker Compose.

## 🛠️ Tech Stack

| Technology          | Purpose                                      |
| ------------------- | -------------------------------------------- |
| Python 3.12         | Backend language                             |
| FastAPI             | REST API framework                           |
| SQLAlchemy          | Database ORM                                 |
| PostgreSQL / SQLite | Database options, depending on configuration |
| Google Gemini API   | AI response generation                       |
| Redis               | Caching, rate limiting, and task messaging   |
| Celery              | Background task processing                   |
| JWT                 | Authentication                               |
| Docker              | Application containerization                 |
| Docker Compose      | Running the API and worker together          |
| Server-Sent Events  | Streaming AI responses                       |

## 🏗️ Architecture

```text
                  Client
                    |
                    v
             FastAPI Application
                    |
          +---------+----------+
          |         |          |
          v         v          v
   Authentication  Redis    Database
          |       Cache &   Conversations
          |       Limits    & Messages
          |
          v
      Gemini API
          |
          v
     AI Response

   Background Processing

   FastAPI --> Redis Broker --> Celery Worker
                                  |
                                  v
                           Background Tasks
```

Redis supports caching and rate limiting while also acting as the Celery message broker. The API and worker can run as separate Docker containers built from the same application image.

## 📁 Project Structure

```text
Production-AI-SaaS-Backend/
├── app/
│   ├── main.py
│   ├── middleware.py
│   ├── celery_app.py
│   ├── tasks.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   └── jobs.py
│   └── services/
│       ├── gemini.py
│       ├── redis_client.py
│       ├── rate_limiter.py
│       ├── ai_usage.py
│       ├── ai_cache.py
│       └── observability.py
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

*The structure above describes the main components; filenames and folders may vary slightly in your local repository.*

## ⚙️ Getting Started

### Prerequisites

- Python 3.12
- Git
- A Google Gemini API key
- A Redis instance for caching, rate limiting, and background jobs
- Docker Desktop (optional, for containerized execution)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Production-AI-SaaS-Backend.git
cd Production-AI-SaaS-Backend
```

Replace `YOUR_USERNAME` with your GitHub username and adjust the repository URL if you choose a different repository name.

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root. Add the variable names expected by your application settings.

Example configuration:

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=replace_with_a_strong_random_secret
REDIS_URL=your_redis_connection_url
DATABASE_URL=your_database_connection_url
```

**Important:** These are example variable names. Confirm that they match your actual application settings before running the project. Use a secure secret, configure the database according to your setup, and never commit `.env` or real credentials to GitHub.

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

**[http://localhost:8000/docs](http://localhost:8000/docs)**

Authentication may be required for protected endpoints.

## 🐳 Running with Docker

Build the application image and start the API and Celery worker:

```bash
docker compose build
docker compose up -d
```

View running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the services:

```bash
docker compose down
```

Docker Compose uses the project's Docker configuration to run the API and worker separately. Ensure your `.env` file contains the required configuration and that the configured database and Redis services are reachable.

## 🔌 API Capabilities

The application includes endpoints for:

- User registration, login, and current-user information.
- Creating and managing conversations and messages.
- Generating and streaming AI responses.
- Submitting background jobs and retrieving their status.
- Health or status checks, depending on the route configuration.

Use `/docs` to inspect the actual routes, schemas, and authentication requirements.

## 🔐 Security Considerations

- Keep API keys and secrets in environment variables.
- Hash passwords instead of storing plaintext passwords.
- Protect private conversation data with authentication and ownership checks.
- Apply rate limits to control excessive API usage.
- Use HTTPS and secure production configuration.
- Review background-job authorization, task status access, database persistence, and error handling before serving real users.

## 🗺️ Roadmap

- [x] FastAPI application and API routing
- [x] JWT authentication
- [x] Database-backed conversations and messages
- [x] Gemini AI integration
- [x] Redis caching and rate limiting
- [x] AI usage tracking
- [x] Celery background task processing
- [x] Structured logging and request observability
- [x] Streaming AI responses
- [x] Docker and Docker Compose configuration
- [ ] Automated CI/CD with GitHub Actions
- [ ] Production deployment and health monitoring
- [ ] Comprehensive automated tests
- [ ] Final production security and reliability review

## 🎯 Project Goal

The goal is to build a reusable foundation for AI-powered SaaS applications, combining AI inference with authentication, usage controls, asynchronous processing, caching, and deployment-oriented infrastructure.

This project is being developed iteratively, with an emphasis on understanding the engineering decisions behind a production-oriented backend.

## 👨‍💻 Author

**Inderjot Singh**

- GitHub: [InderjotSingh17](https://github.com/InderjotSingh17)
- LinkedIn: [Inderjot Singh](https://www.linkedin.com/in/inderjot-singh-0471a6237)

---

*Built with Python, FastAPI, and a focus on production-oriented AI backend engineering.*
