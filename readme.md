simple project to understand AI Agentic codebase

commands:
fastapi dev fast-api.py
ruff format

docker (runs everything - frontend, fast_api, fast_mcp):
docker compose -f docker/docker-compose.yml up --build

Diagram:
Nextjs <-> fast-api <-> lang-graph <-> fast-mcp
              |             |
          sql-Alchemy   Checkpointer(SQLite)