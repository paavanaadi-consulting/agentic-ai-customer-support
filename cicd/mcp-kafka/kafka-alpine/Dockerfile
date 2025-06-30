# Alpine-based minimal Kafka image
FROM alpine:3.18

# Set environment variables
ENV KAFKA_VERSION=2.13-3.6.0
ENV SCALA_VERSION=2.13
ENV KAFKA_HOME=/opt/kafka

# Install dependencies
RUN apk add --no-cache \
    bash \
    openjdk11-jre \
    curl \
    && rm -rf /var/cache/apk/*

# Create kafka user and directories
RUN addgroup -g 1001 kafka && \
    adduser -D -s /bin/bash -u 1001 -G kafka kafka && \
    mkdir -p ${KAFKA_HOME} /var/log/kafka && \
    chown -R kafka:kafka ${KAFKA_HOME} /var/log/kafka

# Download and install Kafka
RUN curl -fSL "https://archive.apache.org/dist/kafka/3.6.0/kafka_${KAFKA_VERSION}.tgz" \
    | tar -xzf - --strip-components=1 -C ${KAFKA_HOME} && \
    chown -R kafka:kafka ${KAFKA_HOME}

# Set working directory
WORKDIR ${KAFKA_HOME}

# Switch to kafka user
USER kafka

# Expose ports
EXPOSE 9092

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD ${KAFKA_HOME}/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 || exit 1

# Default command
CMD ["bin/kafka-server-start.sh", "config/server.properties"]
