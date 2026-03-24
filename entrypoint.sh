#!/bin/sh

# Wait for the database to be ready (optional, but good practice)
# You might want to add a wait-for-it script here if needed.

# Apply database migrations
echo "Applying database migrations..."
export FLASK_APP=run.py
flask db upgrade

# Start the application with sync workers (reverted for stability)
echo "Starting application..."
exec gunicorn -w 3 -b 0.0.0.0:7860 run:app
