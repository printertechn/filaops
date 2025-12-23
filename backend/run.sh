#!/bin/bash
# FilaOps Backend Service Wrapper
# Usage: ./run.sh

cd "$(dirname "$0")"
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
