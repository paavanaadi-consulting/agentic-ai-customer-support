# PostgreSQL Database for Agentic AI Customer Support
FROM postgres:15-alpine

# Set environment variables
ENV POSTGRES_DB=agentic_ai_support
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin123

# Copy initialization scripts
COPY cicd/postgres/init-scripts/ /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1
