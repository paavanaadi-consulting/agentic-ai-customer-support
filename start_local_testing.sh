#!/bin/bash
# Quick Start Script for Local Testing (No Docker)

set -e  # Exit on any error

echo "🚀 Setting up local testing environment..."
echo "========================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the repository root"
    exit 1
fi

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Step 2: Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Step 3: Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Step 5: Set up local configuration
echo "⚙️  Setting up configuration..."
if [ ! -f ".env.local" ]; then
    cp .env.native .env.local
    echo "✅ Created .env.local from .env.native"
else
    echo "✅ .env.local already exists"
fi

# Step 6: Set up SQLite database
echo "🗄️  Setting up SQLite database..."
python3 -c "
import sqlite3
import os

# Create database directory
os.makedirs('data', exist_ok=True)

# Create database and tables
conn = sqlite3.connect('data/test.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS knowledge_articles (
    article_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS query_interactions (
    interaction_id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    agent_response TEXT,
    customer_satisfaction INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
''')

# Insert sample data
sample_customers = [
    ('test_customer_12345', 'John Doe', 'john.doe@example.com', '+1-555-0123'),
    ('test_customer_67890', 'Jane Smith', 'jane.smith@example.com', '+1-555-0456'),
    ('customer_123', 'Alice Johnson', 'alice.johnson@example.com', '+1-555-0789'),
    ('customer_456', 'Bob Wilson', 'bob.wilson@example.com', '+1-555-0101'),
    ('customer_789', 'Carol Brown', 'carol.brown@example.com', '+1-555-0202')
]

cursor.executemany('''
    INSERT OR IGNORE INTO customers (customer_id, name, email, phone) 
    VALUES (?, ?, ?, ?)
''', sample_customers)

sample_articles = [
    ('kb_001', 'How to Reset Password', 'To reset your password, visit the login page and click \"Forgot Password\". You will receive an email with instructions to create a new password. Make sure to check your spam folder if you don\\'t see the email within 5 minutes.', 'account'),
    ('kb_002', 'Support Hours', 'Our support team is available Monday-Friday 9AM-5PM EST. You can reach us through live chat, email at support@example.com, or phone at 1-800-SUPPORT.', 'general'),
    ('kb_003', 'Account Access Issues', 'If you cannot access your account, try these steps: 1) Clear your browser cache and cookies, 2) Try using an incognito/private browsing window, 3) Disable browser extensions temporarily, 4) Try a different browser. If none of these work, contact our support team.', 'account'),
    ('kb_004', 'Payment Problems', 'If you\\'re experiencing payment issues, please check: 1) Your card details are correct, 2) Your card has not expired, 3) You have sufficient funds, 4) Your bank is not blocking the transaction. For persistent issues, contact your bank or our billing department.', 'billing'),
    ('kb_005', 'How to Update Profile', 'To update your profile information: 1) Log into your account, 2) Click on \"Profile\" or \"Account Settings\", 3) Edit the information you want to change, 4) Click \"Save Changes\". Some changes may require email verification.', 'account')
]

cursor.executemany('''
    INSERT OR IGNORE INTO knowledge_articles (article_id, title, content, category) 
    VALUES (?, ?, ?, ?)
''', sample_articles)

conn.commit()
conn.close()
print('✅ SQLite database created with sample data')
"

# Step 7: Set up Kafka (optional)
echo "📡 Setting up Kafka (optional)..."
echo "Do you want to install and start Kafka locally? (y/N)"
read -r kafka_choice
if [[ "$kafka_choice" =~ ^[Yy]$ ]]; then
    if command -v kafka-topics &> /dev/null; then
        echo "✅ Kafka already installed"
        ./scripts/manage_kafka.sh start
    else
        echo "📦 Installing Kafka..."
        ./scripts/install_kafka.sh
        echo "🚀 Starting Kafka..."
        ./scripts/manage_kafka.sh start
    fi
    
    # Update .env.local to use real Kafka
    if [[ -f ".env.local" ]]; then
        echo "⚙️ Updating configuration for Kafka..."
        sed -i '' 's/KAFKA_ENABLED=false/KAFKA_ENABLED=true/' .env.local
        sed -i '' 's/MESSAGE_QUEUE_TYPE=memory/MESSAGE_QUEUE_TYPE=kafka/' .env.local
        echo "KAFKA_BOOTSTRAP_SERVERS=localhost:9092" >> .env.local
    fi
else
    echo "⏭️ Skipping Kafka setup - using in-memory queues"
fi

# Step 8: Run a quick test
echo "🧪 Running quick test..."
python3 scripts/test_native.py --scenario basic

echo ""
echo "🎉 Setup complete! Your local testing environment is ready."
echo ""
echo "Next steps:"
echo "1. Run full tests: python scripts/test_native.py"
echo "2. Run unit tests: python -m pytest tests/ -v"
echo "3. Run specific scenarios: python scripts/test_native.py --scenario [basic|knowledge|response|full|performance]"
echo "4. Check logs: tail -f logs/native_test.log"
echo "5. Add API keys to .env.local for LLM integration (optional)"
echo ""
echo "Local testing components:"
echo "✅ SQLite database (data/test.db)"
echo "✅ In-memory message queues"
echo "✅ Mock MCP servers"
echo "✅ Sample customer data"
echo "✅ Knowledge base articles"
echo ""
echo "Happy testing! 🚀"
