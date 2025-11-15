#!/bin/bash

# MIDI to JSON Converter - Stop Script

echo "Stopping MIDI to JSON Converter..."
docker-compose down

echo ""
echo "✓ Application stopped successfully"
echo ""
echo "To start again, run: ./start.sh"
echo ""
