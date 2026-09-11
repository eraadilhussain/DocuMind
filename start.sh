#!/bin/bash
set -e
# Run database migrations if any (optional, you can add alembic here)
# Start the backend in the background on port 8000
echo "Starting FastAPI backend..."
cd /home/user/app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
# Wait a moment to ensure backend is up
sleep 3
# Start the frontend in the foreground on port 7860
echo "Starting Next.js frontend..."
cd /home/user/app/frontend
export PORT=7860
npm start