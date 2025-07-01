# Multi-stage minimal Kafka build
FROM openjdk:11-jre-slim as base

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Download and extract Kafka
WORKDIR /tmp
RUN curl -fSL "https://archive.apache.org/dist/kafka/3.6.0/kafka_2.13-3.6.0.tgz" \
    | tar -xzf - && \
    mv kafka_2.13-3.6.0 /opt/kafka

# Second stage - minimal runtime
FROM openjdk:11-jre-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Kafka from base stage
COPY --from=base /opt/kafka /opt/kafka

# Create kafka user
RUN groupadd -r kafka && useradd -r -g kafka kafka && \
    mkdir -p /var/log/kafka /tmp/kafka-logs && \
    chown -R kafka:kafka /opt/kafka /var/log/kafka /tmp/kafka-logs

# Set environment
ENV KAFKA_HOME=/opt/kafka
ENV PATH=${KAFKA_HOME}/bin:${PATH}

# Copy configuration
COPY server.properties ${KAFKA_HOME}/config/

WORKDIR ${KAFKA_HOME}
USER kafka

EXPOSE 9092

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD kafka-broker-api-versions.sh --bootstrap-server localhost:9092 || exit 1

CMD ["kafka-server-start.sh", "config/server.properties"]
