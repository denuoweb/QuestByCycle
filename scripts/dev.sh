#!/usr/bin/env bash
set -euo pipefail

# Start Flask development server, Vite dev server, and RQ worker concurrently.
# Use trap to ensure all child processes exit when this script does.
trap 'kill 0' EXIT

# Flask backend with reloader and debugger
poetry run flask --app wsgi:app --debug run &

# Vite frontend dev server
npm run dev &

# Background task worker
poetry run rqworker &

wait
