#!/bin/bash
# Kafka Installation Script for macOS

set -e

echo "🚀 Installing Kafka on macOS"
echo "============================"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS. For other platforms, please install manually."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Install Homebrew if not present
if ! command_exists brew; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew already installed"
fi

# Step 2: Update Homebrew
echo "🔄 Updating Homebrew..."
brew update

# Step 3: Install Java (required for Kafka)
if ! command_exists java; then
    echo "☕ Installing Java..."
    brew install openjdk@11
    
    # Add Java to PATH
    echo 'export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"
else
    echo "✅ Java already installed"
    java -version
fi

# Step 4: Install Kafka
if ! command_exists kafka-topics; then
    echo "📡 Installing Kafka..."
    brew install kafka
else
    echo "✅ Kafka already installed"
fi

# Step 5: Verify installation
echo "🔍 Verifying Kafka installation..."
if command_exists kafka-topics && command_exists kafka-server-start; then
    echo "✅ Kafka installed successfully!"
    
    # Show versions
    echo ""
    echo "📋 Installation Summary:"
    echo "------------------------"
    java -version 2>&1 | head -1
    
    # Get Kafka version
    KAFKA_VERSION=$(ls /opt/homebrew/Cellar/kafka/ 2>/dev/null | head -1 || ls /usr/local/Cellar/kafka/ 2>/dev/null | head -1 || echo "unknown")
    echo "Kafka version: $KAFKA_VERSION"
    
    # Show Kafka paths
    echo ""
    echo "📁 Kafka Paths:"
    echo "---------------"
    KAFKA_PATH=$(brew --prefix kafka)
    echo "Kafka home: $KAFKA_PATH"
    echo "Config files: $KAFKA_PATH/libexec/config/"
    echo "Logs: $KAFKA_PATH/libexec/logs/"
    
else
    echo "❌ Kafka installation failed"
    exit 1
fi

# Step 6: Create Kafka directories
echo "📁 Creating Kafka directories..."
mkdir -p logs/kafka
mkdir -p data/kafka
mkdir -p data/zookeeper

# Step 7: Create configuration files
echo "⚙️ Creating configuration files..."

# Create custom Zookeeper config
cat > config/zookeeper.properties << EOF
# Zookeeper configuration for local development
dataDir=./data/zookeeper
clientPort=2181
maxClientCnxns=0
admin.enableServer=false
tickTime=2000
initLimit=10
syncLimit=5
EOF

# Create custom Kafka server config
cat > config/server.properties << EOF
# Kafka server configuration for local development
broker.id=0
listeners=PLAINTEXT://localhost:9092
advertised.listeners=PLAINTEXT://localhost:9092
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# Log configuration
log.dirs=./data/kafka
num.partitions=1
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

# Log retention
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

# Zookeeper connection
zookeeper.connect=localhost:2181
zookeeper.connection.timeout.ms=18000

# Group coordinator configuration
group.initial.rebalance.delay.ms=0
EOF

echo "✅ Configuration files created in config/"

# Step 8: Create environment setup
echo "🔧 Setting up environment..."

# Add Kafka to PATH in shell profile
SHELL_PROFILE=""
if [[ -n "$ZSH_VERSION" ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ -n "$BASH_VERSION" ]]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [[ -n "$SHELL_PROFILE" ]]; then
    # Check if Kafka PATH is already added
    if ! grep -q "kafka/bin" "$SHELL_PROFILE" 2>/dev/null; then
        echo "" >> "$SHELL_PROFILE"
        echo "# Kafka setup" >> "$SHELL_PROFILE"
        echo "export KAFKA_HOME=\$(brew --prefix kafka)" >> "$SHELL_PROFILE"
        echo "export PATH=\"\$KAFKA_HOME/bin:\$PATH\"" >> "$SHELL_PROFILE"
        echo "✅ Added Kafka to PATH in $SHELL_PROFILE"
    else
        echo "✅ Kafka already in PATH"
    fi
fi

echo ""
echo "🎉 Kafka installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Restart your terminal or run: source ~/.zshrc"
echo "2. Start Kafka: ./scripts/manage_kafka.sh start"
echo "3. Test Kafka: ./scripts/manage_kafka.sh test"
echo ""
echo "Available commands:"
echo "- kafka-topics: Manage topics"
echo "- kafka-console-producer: Send messages"
echo "- kafka-console-consumer: Read messages"
echo "- kafka-server-start: Start Kafka server"
echo "- zookeeper-server-start: Start Zookeeper"
