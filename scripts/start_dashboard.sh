#!/bin/bash
cd "$HOME/ai-dev-team"
source .venv/bin/activate
export PORT=${PORT:-8001}
streamlit run scripts/dashboard_streaming.py --server.port=$PORT --server.address=0.0.0.0
