#!/bin/bash

# MIDI to JSON Converter - Startup Script

set -e

echo "======================================"
echo "MIDI to JSON Converter"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  Note: You can configure AWS S3 credentials either:"
    echo "   1. Edit the .env file now"
    echo "   2. Configure later via the web UI"
    echo ""
fi

# Build and start containers
echo "🚀 Starting MIDI to JSON Converter..."
echo ""

docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check if backend is healthy
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "⚠️  Backend might still be starting up..."
fi

echo ""
echo "======================================"
echo "✓ Application Started Successfully!"
echo "======================================"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:8080"
echo "  Backend API: http://localhost:5000/api/health"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8080 in your browser"
echo "  2. Configure AWS S3 (optional) via the web UI"
echo "  3. Upload MIDI files and convert them to JSON!"
echo ""
