#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
export FLASK_APP=run.py

# Intentamos actualizar. Si falla (porque las tablas ya existen), forzamos el 'stamp' al estado más reciente (head)
if ! flask db upgrade; then
    echo "Warning: Database upgrade failed. Forcing stamp to head to sync migration history..."
    flask db stamp head
fi


# Start the application with gevent-websocket worker
echo "Starting application with geventwebsocket..."
# Usamos el worker específico para WebSockets
exec gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:7860 run:app
