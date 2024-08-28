FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
COPY . .


RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 9393

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9393"]
