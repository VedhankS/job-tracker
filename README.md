# Job Tracker

A full-stack job tracking application built with React, Flask, and PostgreSQL. It includes separate services for authentication, job management, and AI functionality.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** Python, Flask
- **Database:** PostgreSQL
- **AI:** Ollama, ChromaDB
- **Infrastructure:** Docker, Docker Compose, Nginx

## Project Structure

```text
job-tracker/
├── ai-service/
├── api-service/
├── auth-service/
├── frontend/
├── docker-compose.yml
└── nginx.conf
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Ollama running on the host machine
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/VedhankS/job-tracker.git
   cd job-tracker
   ```

2. Start the application:

   ```bash
   docker compose up --build
   ```

3. Open the application:

   ```text
   http://localhost:5173
   ```

## Services

| Service | Description |
|---|---|
| Frontend | React user interface |
| Auth Service | User registration and login |
| API Service | Job management API |
| AI Service | AI-related functionality |
| Database | PostgreSQL data storage |
| Nginx | Reverse proxy |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Register a user |
| POST | `/login` | Log in |
| GET | `/jobs` | Retrieve jobs |
| POST | `/jobs` | Create a job |
| DELETE | `/jobs/:id` | Delete a job |
| GET | `/health` | Check API health |

API requests are routed through Nginx at `http://localhost:8080`.

## Stopping the Application

```bash
docker compose down
```

To remove the database volume as well:

```bash
docker compose down -v
```

**Note:** Removing volumes deletes persisted database data. Configure production secrets and database credentials securely before deployment.
**Note:** Copy .env.example to .env and fill in the values before running docker compose up
