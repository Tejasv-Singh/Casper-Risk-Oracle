# Build Stage for Casper Client
FROM rust:slim-bullseye as builder

RUN apt-get update && apt-get install -y pkg-config libssl-dev git
# Install casper-client
# Note: Cloning and building or cargo install. cargo install is easiest for now.
RUN cargo install casper-client

# Runtime Stage
FROM python:3.10-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    curl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy casper-client from builder
COPY --from=builder /usr/local/cargo/bin/casper-client /usr/bin/casper-client

# Set working directory
WORKDIR /app

# Copy Requirements and Install
# (Create requirements.txt on the fly if needed, or assume it exists. 
# Plan said copy it. I need to make sure it exists first. 
# Current directory has no requirements.txt, only venv. 
# I will create a Requirements file in the next step or manually install packages in Dockerfile)
# Let's create requirements.txt first or install directly. 
# Direct install is robust for single file project.
RUN pip install requests

# Copy Agent Code and Secrets
COPY oracle_agent.py .
COPY "Account 1_secret_key.pem" .

# Setup Output Directory for logs (so we can mount it)
RUN mkdir -p ../risk-dashboard/public

# Run Agent
CMD ["python", "oracle_agent.py"]
