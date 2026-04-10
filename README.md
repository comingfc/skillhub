# SkillHub - Self-hosted Agent Skills Platform

A self-hosted platform for teams to share agent skills privately with governance.

## Features

- **Skill Packages**: Publish skill packages (ZIP) with semantic versioning, tags (beta/stable), and `latest` tracking
- **Discovery**: Full-text search with filters (namespace, downloads, rating, time)
- **Team Namespaces**: Organize skills under team/global namespaces with roles (Owner/Admin/Member)
- **Review & Governance**: Team admins review within their namespace; platform admins control global promotion
- **Audit Logging**: All governance actions recorded for compliance
- **Social Features**: Favorite skills, rate and track downloads

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: React 18+ / TypeScript / Vite
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Storage**: MinIO / S3-compatible

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+

### Development

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production

```bash
docker-compose up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│         Vite + TypeScript + TailwindCSS                  │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │   API Gateway  │
                    └───────┬───────┘
                            │
┌───────────────────────────▼───────────────────────────┐
│                    Backend (FastAPI)                   │
│  Auth Service | Skills Service | Namespace Service    │
└───────────────────────────────────────────────────────────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │PostgreSQL│  │  Redis  │  │  MinIO  │
    └─────────┘  └─────────┘  └─────────┘
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT
