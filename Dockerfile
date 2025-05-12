# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any dependencies needed by the Flask app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the tests into the container
COPY test_app.py /app/test_app.py

# Run the tests
RUN python /app/test_app.py

# Expose port 5000 (the default Flask port)
EXPOSE 5000

# Set the environment variable for Flask (if needed)
ENV FLASK_APP=app.py

# Command to run the Flask app
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

# ... (your existing Dockerfile)



# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"] # Keep this as the last command