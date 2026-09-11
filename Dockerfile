FROM python:3.10-slim
# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean
# Create user for Hugging Face Spaces (user ID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
# Set working directory
WORKDIR $HOME/app
# Copy application files and change ownership
COPY --chown=user:user . $HOME/app/
# Install backend dependencies
WORKDIR $HOME/app/backend
RUN pip install --no-cache-dir -r requirements.txt
# Install frontend dependencies and build
WORKDIR $HOME/app/frontend
RUN npm install
RUN npm run build
# Make the start script executable
WORKDIR $HOME/app
RUN chmod +x start.sh
# Create the data directory for persistent storage
RUN mkdir -p $HOME/app/data
# Set environment variables so the backend writes to the persistent data folder
ENV DATABASE_URL="sqlite:////home/user/app/data/documind.db"
ENV QDRANT_PATH="/home/user/app/data/qdrant_data"
ENV UPLOAD_DIR="/home/user/app/data/uploads"
# Expose port 7860 (Hugging Face requirement)
EXPOSE 7860
# Run the start script
CMD ["./start.sh"]