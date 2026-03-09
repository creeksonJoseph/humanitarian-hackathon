# -----------------------------------------------------------------------------
# Stage 1: Build environment
# -----------------------------------------------------------------------------
FROM python:3.8-slim AS builder

# Set environment variables to optimize Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a virtual environment
RUN python -m venv /opt/venv

# Make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies, including gunicorn for production usage
# Wheels will be cached in the image layer but won't bloat the final image
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# -----------------------------------------------------------------------------
# Stage 2: Production environment
# -----------------------------------------------------------------------------
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app:create_app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user and group for better security
RUN addgroup --system appuser && adduser --system --group appuser

# Copy the rest of the application code
COPY . .

# Ensure the non-root user has access to the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port (Render will override this via the PORT environment variable)
EXPOSE 10000

# Run the application using Gunicorn
# Binds to 0.0.0.0 and uses Render's dynamic PORT environment variable (defaulting to 10000)
# Uses "app:create_app()" since `app.py` has `app = create_app()` but the app logic
# requires the application factory to be called to properly initialize blueprints and the DB.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} 'app:create_app()'"]
