FROM python:3.12-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your application code
COPY . .

# Expose ports
EXPOSE 8080 8001

# Start your services
CMD ["python", "app.py"]
