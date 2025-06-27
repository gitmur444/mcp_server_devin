FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY wrapper_requirements.txt .
RUN pip install --no-cache-dir -r wrapper_requirements.txt

# Copy MCP server package
COPY mcp_server_devin_pkg/ ./mcp_server_devin_pkg/
COPY __init__.py .
COPY setup.py .

# Install MCP server package
RUN pip install -e .

# Copy HTTP wrapper
COPY mcp_http_wrapper.py .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the wrapper
CMD ["uvicorn", "mcp_http_wrapper:app", "--host", "0.0.0.0", "--port", "8000"]
