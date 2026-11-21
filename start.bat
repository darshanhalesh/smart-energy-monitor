@echo off

if not exist .env (
    copy .env.example .env >nul
    echo Created .env from .env.example
)

echo Starting Smart Energy Monitor...
docker compose up --build
