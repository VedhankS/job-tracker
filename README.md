# Job Tracker - Full-Stack Microservices Application

A containerized full-stack application for tracking job applications using a microservices architecture with independent Flask APIs, a React frontend, a PostgreSQL database, and an Nginx reverse proxy.

## Architecture & Tech Stack

This project uses 5 independent Docker containers:
- **Frontend (`frontend`)**: React + Vite, Tailwind CSS v4, React Router.
- **Authentication Service (`auth-service`)**: Python Flask API for user registration, login, and JWT generation.
- **Jobs API Service (`api-service`)**: Python Flask API for job application CRUD operations.
- **Database (`db`)**: PostgreSQL database.
- **Reverse Proxy (`nginx`)**: Nginx server routing traffic to the Flask microservices.

## Getting Started

### Prerequisites
- Docker Desktop
- Git

### Installation & Running

1. Clone the repository:
   ```bash
   git clone [https://github.com/VedhankS/job-tracker.git](https://github.com/VedhankS/job-tracker.git)
   cd job-tracker
   ```

2. Start the Docker Compose cluster:
   ```bash
   docker compose up --build -d
   ```

3. Access the application:
   - Navigate to `http://127.0.0.1:5173` in your browser.
   - The Nginx reverse proxy runs internally on port 8080.

### Stopping the Application

Stop containers and preserve database data:
```bash
docker compose down
```

Stop containers and wipe database data:
```bash
docker compose down -v
```

## Project Structure

```text
job-tracker/
├── api-service/          # Flask app for Job CRUD (Port 5000)
├── auth-service/         # Flask app for JWT Auth (Port 5001)
├── frontend/             # React/Vite application (Port 5173)
├── nginx.conf            # Nginx routing (Port 8080)
├── docker-compose.yml    # Docker orchestration
└── README.md
```

## API Endpoints & Routing

| Route | Method | Handled By | Description |
|---|---|---|---|
| `/register` | POST | `auth-service` | Creates a new user account. |
| `/login` | POST | `auth-service` | Authenticates user and returns JWT. |
| `/jobs` | GET | `api-service` | Retrieves all jobs for the authenticated user. |
| `/jobs` | POST | `api-service` | Adds a new job application. |
| `/jobs/<id>` | DELETE | `api-service` | Deletes a specific job application. |
| `/health` | GET | `api-service` | Verifies the API is online. |

## Notes for macOS Users
If `localhost:5173` fails to load, use `http://127.0.0.1:5173` directly to bypass IPv6 network resolution issues.
