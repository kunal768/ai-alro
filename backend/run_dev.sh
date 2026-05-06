#!/usr/bin/env bash
# Start all backend services for local development.
# Run from the backend/ directory:
#   bash run_dev.sh
#
# Requires:
#   .venv/   — Python 3.13 venv with all deps installed
#   .env     — copy of .env.example with real API key(s) filled in
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
    echo "No .venv found. Create it first:"
    echo "  python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Load .env if present (exports ANTHROPIC_API_KEY etc. into the shell)
if [[ -f ".env" ]]; then
    set -a; source ".env"; set +a
fi

source .venv/bin/activate

cleanup() {
    echo ""
    echo "Stopping services..."
    kill "$ERP_PID" "$INTAKE_PID" "$REASONER_PID" 2>/dev/null || true
    wait "$ERP_PID" "$INTAKE_PID" "$REASONER_PID" 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

echo "Starting ERP Service on :8001 ..."
uvicorn erp_service.main:app --host 0.0.0.0 --port 8001 --log-level warning &
ERP_PID=$!

echo "Starting Intake Agent on :8002 ..."
uvicorn intake_agent.main:app --host 0.0.0.0 --port 8002 --log-level warning &
INTAKE_PID=$!

echo "Starting Reasoner Agent on :8004 ..."
uvicorn reasoner_agent.main:app --host 0.0.0.0 --port 8004 --log-level warning &
REASONER_PID=$!

# Wait until /health on each service responds
for port in 8001 8002 8004; do
    for _ in $(seq 1 20); do
        if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
done

echo ""
echo "Services ready:"
echo "  ERP Service    → http://localhost:8001  (docs: /docs)"
echo "  Intake Agent   → http://localhost:8002  (docs: /docs)"
echo "  Reasoner Agent → http://localhost:8004  (docs: /docs)"
echo ""
echo "LLM provider: ${LLM_PROVIDER:-anthropic}  model: ${LLM_MODEL:-default}"
echo ""
echo "Run tests in another terminal:"
echo "  cd backend && python test_intake.py"
echo "  cd backend && python test_reasoner.py"
echo ""
echo "Press Ctrl+C to stop all services."

wait
