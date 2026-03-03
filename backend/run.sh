#!/usr/bin/env bash

# Simple dev runner for the NetZero AI backend.
# Activates local virtual environment if present, then starts uvicorn.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -d ".venv" ]; then
  # Try common virtualenv locations (POSIX and Windows via Git Bash)
  if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
  elif [ -f ".venv/Scripts/activate" ]; then
    source ".venv/Scripts/activate"
  fi
fi

exec uvicorn app.main:app --reload --port 8000

