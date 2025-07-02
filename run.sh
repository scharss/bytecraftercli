#!/bin/bash

# Check for .env file and essential variables
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create it and add your GEMINI_API_KEY."
    exit 1
fi

if ! grep -q "GEMINI_API_KEY" .env || [[ "$(grep GEMINI_API_KEY .env | cut -d '=' -f2)" == *"YOUR_API_KEY_HERE"* ]] || [[ -z "$(grep GEMINI_API_KEY .env | cut -d '=' -f2)" ]]; then
    echo "Error: GEMINI_API_KEY is not set in the .env file. Please add it to continue."
    exit 1
fi

# 1. Build and start services in detached mode
echo "Building and starting services..."
docker-compose up -d --build

# 2. Attach to the bytecrafter container for an interactive session
echo "Attaching to the Bytecrafter CLI..."
echo "Type 'exit' or 'quit' to end the session."
docker-compose exec bytecrafter python -m bytecrafter.main "$@"

# 3. Optional: Stop services on exit
echo "Shutting down services..."
docker-compose down 