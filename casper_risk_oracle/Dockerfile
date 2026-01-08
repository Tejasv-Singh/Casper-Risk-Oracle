# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# (Assuming you put casper-python-sdk in requirements.txt)
RUN pip install casper-python-sdk

# Run the oracle agent when the container launches
CMD ["python", "oracle_agent.py"]
