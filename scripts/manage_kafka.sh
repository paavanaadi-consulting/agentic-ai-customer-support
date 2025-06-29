#!/bin/bash
# Kafka Management Script for Local Development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KAFKA_LOG_DIR="$PROJECT_ROOT/logs/kafka"
KAFKA_DATA_DIR="$PROJECT_ROOT/data/kafka"
ZK_DATA_DIR="$PROJECT_ROOT/data/zookeeper"
CONFIG_DIR="$PROJECT_ROOT/config"

# Ensure directories exist
mkdir -p "$KAFKA_LOG_DIR" "$KAFKA_DATA_DIR" "$ZK_DATA_DIR" "$CONFIG_DIR"

# Function to check if process is running
is_running() {
    local service=$1
    case $service in
        zookeeper)
            pgrep -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" > /dev/null
            ;;
        kafka)
            pgrep -f "kafka.Kafka" > /dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to wait for service to start
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service to start on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ $service is ready on port $port"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to start Zookeeper
start_zookeeper() {
    if is_running zookeeper; then
        echo "✅ Zookeeper is already running"
        return 0
    fi
    
    echo "🚀 Starting Zookeeper..."
    
    # Use custom config if available, otherwise use default
    local zk_config="$CONFIG_DIR/zookeeper.properties"
    if [[ ! -f "$zk_config" ]]; then
        zk_config="$(brew --prefix kafka)/libexec/config/zookeeper.properties"
    fi
    
    nohup zookeeper-server-start "$zk_config" > "$KAFKA_LOG_DIR/zookeeper.log" 2>&1 &
    local zk_pid=$!
    echo $zk_pid > "$KAFKA_LOG_DIR/zookeeper.pid"
    
    if wait_for_service "Zookeeper" 2181; then
        echo "✅ Zookeeper started successfully (PID: $zk_pid)"
        return 0
    else
        echo "❌ Failed to start Zookeeper"
        return 1
    fi
}

# Function to start Kafka
start_kafka() {
    if is_running kafka; then
        echo "✅ Kafka is already running"
        return 0
    fi
    
    echo "🚀 Starting Kafka..."
    
    # Use custom config if available, otherwise use default
    local kafka_config="$CONFIG_DIR/server.properties"
    if [[ ! -f "$kafka_config" ]]; then
        kafka_config="$(brew --prefix kafka)/libexec/config/server.properties"
    fi
    
    nohup kafka-server-start "$kafka_config" > "$KAFKA_LOG_DIR/kafka.log" 2>&1 &
    local kafka_pid=$!
    echo $kafka_pid > "$KAFKA_LOG_DIR/kafka.pid"
    
    if wait_for_service "Kafka" 9092; then
        echo "✅ Kafka started successfully (PID: $kafka_pid)"
        return 0
    else
        echo "❌ Failed to start Kafka"
        return 1
    fi
}

# Function to stop services
stop_service() {
    local service=$1
    local pid_file="$KAFKA_LOG_DIR/${service}.pid"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🛑 Stopping $service (PID: $pid)..."
            kill $pid
            
            # Wait for process to stop
            local attempts=0
            while ps -p $pid > /dev/null 2>&1 && [ $attempts -lt 10 ]; do
                sleep 1
                attempts=$((attempts + 1))
            done
            
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚠️  Force killing $service (PID: $pid)..."
                kill -9 $pid
            fi
            
            echo "✅ $service stopped"
        fi
        rm -f "$pid_file"
    else
        # Fallback: kill by process name
        if is_running $service; then
            echo "🛑 Stopping $service..."
            case $service in
                zookeeper)
                    pkill -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" || true
                    ;;
                kafka)
                    pkill -f "kafka.Kafka" || true
                    ;;
            esac
            echo "✅ $service stopped"
        else
            echo "ℹ️  $service is not running"
        fi
    fi
}

# Function to show status
show_status() {
    echo "📊 Kafka Services Status"
    echo "========================"
    
    # Check Zookeeper
    if is_running zookeeper; then
        local zk_pid=$(pgrep -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" | head -1)
        echo "✅ Zookeeper: Running (PID: $zk_pid)"
    else
        echo "❌ Zookeeper: Not running"
    fi
    
    # Check Kafka
    if is_running kafka; then
        local kafka_pid=$(pgrep -f "kafka.Kafka" | head -1)
        echo "✅ Kafka: Running (PID: $kafka_pid)"
    else
        echo "❌ Kafka: Not running"
    fi
    
    # Check ports
    echo ""
    echo "🔌 Port Status:"
    if nc -z localhost 2181 2>/dev/null; then
        echo "✅ Zookeeper port 2181: Open"
    else
        echo "❌ Zookeeper port 2181: Closed"
    fi
    
    if nc -z localhost 9092 2>/dev/null; then
        echo "✅ Kafka port 9092: Open"
    else
        echo "❌ Kafka port 9092: Closed"
    fi
}

# Function to create topics
create_topics() {
    echo "📋 Creating default topics..."
    
    local topics=(
        "customer-queries"
        "agent-events"
        "knowledge-updates"
        "response-events"
        "test-topic"
    )
    
    for topic in "${topics[@]}"; do
        kafka-topics --create \
            --topic "$topic" \
            --bootstrap-server localhost:9092 \
            --partitions 3 \
            --replication-factor 1 \
            --if-not-exists 2>/dev/null && echo "✅ Topic created: $topic" || echo "ℹ️  Topic exists: $topic"
    done
}

# Function to list topics
list_topics() {
    echo "📋 Available topics:"
    kafka-topics --list --bootstrap-server localhost:9092 | sort
}

# Function to test Kafka
test_kafka() {
    echo "🧪 Testing Kafka functionality..."
    
    local test_topic="test-topic-$(date +%s)"
    
    # Create test topic
    echo "1. Creating test topic: $test_topic"
    kafka-topics --create \
        --topic "$test_topic" \
        --bootstrap-server localhost:9092 \
        --partitions 1 \
        --replication-factor 1
    
    # Send test message
    echo "2. Sending test message..."
    local test_message="Test message from $(date)"
    echo "$test_message" | kafka-console-producer --topic "$test_topic" --bootstrap-server localhost:9092
    
    # Read test message
    echo "3. Reading test message..."
    local received_message
    received_message=$(kafka-console-consumer \
        --topic "$test_topic" \
        --bootstrap-server localhost:9092 \
        --from-beginning \
        --max-messages 1 \
        --timeout-ms 5000 2>/dev/null || echo "")
    
    # Verify message
    if [[ "$received_message" == "$test_message" ]]; then
        echo "✅ Test passed! Message sent and received successfully"
    else
        echo "❌ Test failed! Expected: '$test_message', Got: '$received_message'"
    fi
    
    # Clean up test topic
    echo "4. Cleaning up test topic..."
    kafka-topics --delete --topic "$test_topic" --bootstrap-server localhost:9092
    
    echo "🎉 Kafka test completed!"
}

# Function to show logs
show_logs() {
    local service=${1:-all}
    
    case $service in
        zookeeper|zk)
            echo "📜 Zookeeper logs:"
            tail -f "$KAFKA_LOG_DIR/zookeeper.log"
            ;;
        kafka)
            echo "📜 Kafka logs:"
            tail -f "$KAFKA_LOG_DIR/kafka.log"
            ;;
        all|*)
            echo "📜 Recent logs:"
            echo "--- Zookeeper ---"
            tail -10 "$KAFKA_LOG_DIR/zookeeper.log" 2>/dev/null || echo "No Zookeeper logs"
            echo ""
            echo "--- Kafka ---"
            tail -10 "$KAFKA_LOG_DIR/kafka.log" 2>/dev/null || echo "No Kafka logs"
            ;;
    esac
}

# Function to clean up
cleanup() {
    echo "🧹 Cleaning up Kafka data..."
    
    # Stop services first
    stop_service kafka
    stop_service zookeeper
    
    # Remove data directories
    echo "Removing data directories..."
    rm -rf "$KAFKA_DATA_DIR"/* 2>/dev/null || true
    rm -rf "$ZK_DATA_DIR"/* 2>/dev/null || true
    
    # Remove logs
    echo "Removing log files..."
    rm -f "$KAFKA_LOG_DIR"/*.log 2>/dev/null || true
    rm -f "$KAFKA_LOG_DIR"/*.pid 2>/dev/null || true
    
    echo "✅ Cleanup completed"
}

# Main command handler
case "${1:-}" in
    start)
        echo "🚀 Starting Kafka services..."
        start_zookeeper
        sleep 3
        start_kafka
        sleep 5
        create_topics
        echo "✅ All services started successfully!"
        ;;
    stop)
        echo "🛑 Stopping Kafka services..."
        stop_service kafka
        stop_service zookeeper
        echo "✅ All services stopped"
        ;;
    restart)
        echo "🔄 Restarting Kafka services..."
        stop_service kafka
        stop_service zookeeper
        sleep 2
        start_zookeeper
        sleep 3
        start_kafka
        sleep 5
        create_topics
        echo "✅ Services restarted successfully!"
        ;;
    status)
        show_status
        ;;
    topics)
        list_topics
        ;;
    create-topics)
        create_topics
        ;;
    test)
        test_kafka
        ;;
    logs)
        show_logs "${2:-all}"
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        echo "Kafka Management Script"
        echo "======================="
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start         Start Zookeeper and Kafka services"
        echo "  stop          Stop all services"
        echo "  restart       Restart all services"
        echo "  status        Show service status"
        echo "  topics        List all topics"
        echo "  create-topics Create default topics"
        echo "  test          Test Kafka functionality"
        echo "  logs [service] Show logs (zookeeper, kafka, or all)"
        echo "  cleanup       Stop services and clean data"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start all services"
        echo "  $0 test               # Test Kafka"
        echo "  $0 logs kafka         # Show Kafka logs"
        echo "  $0 status             # Check service status"
        ;;
    *)
        echo "❌ Unknown command: ${1:-}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
