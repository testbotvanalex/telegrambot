#!/bin/bash
echo "🐳 Docker build + run"
docker build -t telegram-bot .
docker run --env-file .env -p 8080:8080 telegram-bot
