#!/bin/sh

# Wait for the database to be ready (optional, but good practice)
# You might want to add a wait-for-it script here if needed.

# Apply database migrations
echo "Applying database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn -w 4 -b 0.0.0.0:5000 run:app
