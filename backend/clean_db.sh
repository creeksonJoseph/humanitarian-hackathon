#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the backend directory (where this script is located)
cd "$(dirname "$0")"

echo "🧹 Dropping all database tables..."

# Activate virtual environment
source myenv/bin/activate

# Safely export environment variables from config/.env
set -o allexport
source config/.env
set +o allexport

# Run the Flask clean-db command
flask clean-db

echo "✅ Database cleaned successfully."
