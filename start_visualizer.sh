#!/bin/bash

# CSV 3D Visualizer Startup Script
echo "Starting CSV 3D Visualizer..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the Trame application
echo "Starting Trame application on http://localhost:8080"
python trame_visualizer.py --port 8080

echo "Application stopped."