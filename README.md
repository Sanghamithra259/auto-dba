# Auto-DBA

A multi-agent system that converts natural language to SQL, audits it for security, and executes it on a cloud database.

## Architecture

- **Orchestration**: LangGraph
- **Database**: Supabase 
- **API**: FastAPI
- **Deployment**: Google Cloud Run (Docker)
- **Package Manager**: uv

## Setup

1. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run locally:
   ```bash
   uv run uvicorn src.main:app --reload
   ```

## Environment Variables

Copy `.env.example` to `.env` and fill in your Supabase credentials.
