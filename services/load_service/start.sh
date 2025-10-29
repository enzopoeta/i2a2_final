#!/bin/bash

# Start RabbitMQ worker in background
python rabbitmq_worker.py &
WORKER_PID=$!

# Start FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $WORKER_PID $API_PID 2>/dev/null
    wait $WORKER_PID $API_PID 2>/dev/null
    exit 0
}

# Trap termination signals
trap cleanup SIGTERM SIGINT

# Wait for both processes
wait -n

# If one process dies, kill the other
cleanup

