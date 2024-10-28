FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN useradd -m -d /app appuser
USER appuser

# Expose the port used by the application
EXPOSE 8080

# Command to start the Flask development server
CMD exec python -m flask run --host=0.0.0.0 --port=8080