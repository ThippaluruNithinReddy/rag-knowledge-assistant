#!/bin/bash
# start.sh
# Purpose: startup script for Render deployment
# Render runs this command to start the FastAPI server

uvicorn app.main:app --host 0.0.0.0 --port $PORT
