#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the backend directory (where this script is located)
cd "$(dirname "$0")"

echo "🚀 Initializing and seeding the database..."

# Activate virtual environment
source myenv/bin/activate

# Safely export environment variables from config/.env
set -o allexport
source config/.env
set +o allexport

# Run DB commands
flask init-db
flask seed-db

echo "✅ Database initialized and seeded successfully."
