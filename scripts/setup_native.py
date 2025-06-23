#!/usr/bin/env python3
"""
Local Native Setup Script - No Docker Required
Sets up the repository for local testing without Docker components
"""
import os
import sys
import subprocess
import platform
import json
from pathlib import Path

def print_step(step, description):
    print(f"\n🔧 Step {step}: {description}")
    print("=" * 50)

def run_command(cmd, description, check=True):
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please install Python 3.11 or higher")
        return False

def setup_virtual_environment():
    """Create and activate virtual environment"""
    print_step(1, "Setting up Python Virtual Environment")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        success = run_command(f"{sys.executable} -m venv venv", "Creating virtual environment")
        if not success:
            print("❌ Failed to create virtual environment")
            return False
    
    # Determine activation script path
    if platform.system() == "Windows":
        activate_path = "venv\\Scripts\\activate"
        pip_path = "venv\\Scripts\\pip"
    else:
        activate_path = "venv/bin/activate"
        pip_path = "venv/bin/pip"
    
    print(f"✅ Virtual environment created")
    print(f"📝 To activate manually: source {activate_path}")
    
    return pip_path

def install_dependencies(pip_path):
    """Install Python dependencies"""
    print_step(2, "Installing Python Dependencies")
    
    # Install requirements
    success = run_command(f"{pip_path} install -r requirements.txt", "Installing requirements")
    if not success:
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def setup_local_database():
    """Setup local SQLite database for testing"""
    print_step(3, "Setting up Local Database (SQLite)")
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Create SQLite schema
    sqlite_schema = """
-- Customer Support Database Schema for SQLite
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
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

CREATE TABLE IF NOT EXISTS knowledge_articles (
    article_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Insert sample data
INSERT OR IGNORE INTO customers (customer_id, name, email, phone) VALUES 
('test_customer_12345', 'John Doe', 'john.doe@example.com', '+1-555-0123'),
('test_customer_67890', 'Jane Smith', 'jane.smith@example.com', '+1-555-0456'),
('customer_123', 'Alice Johnson', 'alice.johnson@example.com', '+1-555-0789');

INSERT OR IGNORE INTO knowledge_articles (article_id, title, content, category) VALUES 
('kb_001', 'How to Reset Password', 'To reset your password, visit the login page and click "Forgot Password". Follow the email instructions.', 'account'),
('kb_002', 'Support Hours', 'Our support team is available Monday-Friday 9AM-5PM EST.', 'general'),
('kb_003', 'Account Access Issues', 'If you cannot access your account, try clearing your browser cache or contact support.', 'account');
"""
    
    with open("data/schema.sql", "w") as f:
        f.write(sqlite_schema)
    
    print("✅ SQLite database schema created")
    return True

def create_local_config():
    """Create local configuration files"""
    print_step(4, "Creating Local Configuration")
    
    # Create .env.local for native testing
    env_config = """# Local Native Testing Configuration (No Docker)

# Database Configuration (SQLite)
DATABASE_URL=sqlite:///data/customer_support_local.db
DB_TYPE=sqlite
DB_PATH=data/customer_support_local.db

# In-Memory Alternatives (for testing without external services)
USE_MEMORY_QUEUE=true
USE_MEMORY_CACHE=true
USE_MEMORY_VECTOR_DB=true

# MCP Server Configuration (Local Ports)
MCP_DATABASE_ENABLED=true
MCP_DATABASE_HOST=localhost
MCP_DATABASE_PORT=8001

MCP_KAFKA_ENABLED=false  # Disabled for native testing
MCP_AWS_ENABLED=false    # Disabled for native testing

# A2A Agent Configuration
A2A_QUERY_AGENT_PORT=8101
A2A_KNOWLEDGE_AGENT_PORT=8102
A2A_RESPONSE_AGENT_PORT=8103
A2A_COORDINATOR_PORT=8104

# LLM Configuration (Optional - add your keys)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/local_test.log

# Test Configuration
TEST_MODE=true
MOCK_EXTERNAL_SERVICES=true
"""
    
    with open(".env.local", "w") as f:
        f.write(env_config)
    
    print("✅ Local configuration created (.env.local)")
    return True

def setup_logging():
    """Setup logging directories"""
    print_step(5, "Setting up Logging")
    
    os.makedirs("logs", exist_ok=True)
    print("✅ Logs directory created")
    return True

def create_native_test_runner():
    """Create a test runner for native testing"""
    print_step(6, "Creating Native Test Runner")
    
    test_runner_code = '''#!/usr/bin/env python3
"""
Native Test Runner - No Docker Required
Run A2A tests with in-memory implementations
"""
import asyncio
import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/native_test.log')
    ]
)
logger = logging.getLogger(__name__)


class InMemoryMCPDatabase:
    """In-memory MCP database for testing"""
    
    def __init__(self):
        self.db_path = "data/customer_support_local.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        os.makedirs("data", exist_ok=True)
        
        # Create tables if they don't exist
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        with open("data/schema.sql", "r") as f:
            schema = f.read()
            conn.executescript(schema)
        
        conn.close()
        logger.info("SQLite database initialized")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MCP tool calls with SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if tool_name == "query_database":
                query = arguments.get("query", "")
                params = arguments.get("params", [])
                
                cursor.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "success": True,
                    "data": results,
                    "row_count": len(results)
                }
            
            elif tool_name == "get_customer_context":
                customer_id = arguments.get("customer_id")
                
                cursor.execute("""
                    SELECT c.*, COUNT(st.ticket_id) as ticket_count
                    FROM customers c
                    LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
                    WHERE c.customer_id = ?
                    GROUP BY c.customer_id
                """, (customer_id,))
                
                result = cursor.fetchone()
                
                return {
                    "success": True,
                    "customer_context": dict(result) if result else None
                }
            
            elif tool_name == "search_knowledge_base":
                search_term = arguments.get("search_term", "")
                limit = arguments.get("limit", 10)
                
                cursor.execute("""
                    SELECT * FROM knowledge_articles 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (f"%{search_term}%", f"%{search_term}%", limit))
                
                results = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "success": True,
                    "articles": results
                }
            
            elif tool_name == "save_interaction":
                interaction_data = arguments.get("interaction_data", {})
                
                cursor.execute("""
                    INSERT INTO query_interactions 
                    (interaction_id, query_id, customer_id, query_text, agent_response, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    interaction_data.get("interaction_id", f"int_{int(datetime.now().timestamp())}"),
                    interaction_data.get("query_id"),
                    interaction_data.get("customer_id"),
                    interaction_data.get("query_text"),
                    interaction_data.get("agent_response"),
                    interaction_data.get("created_at", datetime.now().isoformat())
                ))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": "Interaction saved successfully"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        
        except Exception as e:
            logger.error(f"Database operation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        finally:
            conn.close()


class NativeA2AAgent:
    """Simplified A2A agent for native testing"""
    
    def __init__(self, agent_id: str, agent_type: str, port: int):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.port = port
        self.running = False
        self.mcp_db = InMemoryMCPDatabase()
        self.processed_items = []
        
        logger.info(f"Created {agent_type} agent: {agent_id}")
    
    async def start(self):
        """Start the agent"""
        self.running = True
        logger.info(f"Agent {self.agent_id} started (simulated port {self.port})")
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def call_mcp_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]):
        """Call MCP tool (simulated)"""
        if server_id == "mcp_database":
            return await self.mcp_db.call_tool(tool_name, arguments)
        else:
            return {"success": False, "error": f"Unknown MCP server: {server_id}"}


class NativeQueryAgent(NativeA2AAgent):
    """Native query agent"""
    
    def __init__(self):
        super().__init__("native-query-agent", "query", 8101)
    
    async def process_query(self, customer_id: str, query: str):
        """Process customer query"""
        logger.info(f"Processing query from {customer_id}: {query}")
        
        # Get customer context
        customer_result = await self.call_mcp_tool(
            "mcp_database", 
            "get_customer_context", 
            {"customer_id": customer_id}
        )
        
        # Search knowledge base
        knowledge_result = await self.call_mcp_tool(
            "mcp_database",
            "search_knowledge_base",
            {"search_term": query, "limit": 3}
        )
        
        # Save interaction
        interaction_result = await self.call_mcp_tool(
            "mcp_database",
            "save_interaction",
            {
                "interaction_data": {
                    "query_id": f"query_{int(datetime.now().timestamp())}",
                    "customer_id": customer_id,
                    "query_text": query,
                    "agent_response": "Query processed by native agent",
                    "created_at": datetime.now().isoformat()
                }
            }
        )
        
        result = {
            "customer_context": customer_result.get("customer_context"),
            "knowledge_articles": knowledge_result.get("articles", []),
            "interaction_saved": interaction_result.get("success", False)
        }
        
        self.processed_items.append(result)
        logger.info(f"Query processed successfully: {len(self.processed_items)} total")
        
        return result


async def run_native_tests():
    """Run native A2A tests"""
    print("🚀 Starting Native A2A Testing (No Docker)")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    # Create agents
    query_agent = NativeQueryAgent()
    
    try:
        # Start agents
        await query_agent.start()
        
        # Test scenarios
        test_scenarios = [
            ("test_customer_12345", "How do I reset my password?"),
            ("test_customer_67890", "What are your support hours?"),
            ("customer_123", "I can't access my account"),
        ]
        
        print(f"\\n📋 Running {len(test_scenarios)} test scenarios...")
        
        for i, (customer_id, query) in enumerate(test_scenarios, 1):
            print(f"\\n🔍 Test {i}: {query}")
            print("-" * 30)
            
            result = await query_agent.process_query(customer_id, query)
            
            if result["customer_context"]:
                print(f"✅ Customer found: {result['customer_context']['name']}")
            else:
                print(f"⚠️  Customer not found: {customer_id}")
            
            print(f"📚 Knowledge articles found: {len(result['knowledge_articles'])}")
            
            if result["interaction_saved"]:
                print("💾 Interaction saved successfully")
            else:
                print("❌ Failed to save interaction")
            
            # Brief pause between tests
            await asyncio.sleep(0.5)
        
        print(f"\\n🎉 Native Testing Complete!")
        print(f"Total queries processed: {len(query_agent.processed_items)}")
        print("Check logs/native_test.log for detailed logs")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        logger.error(f"Testing failed: {e}")
    
    finally:
        await query_agent.stop()


if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Run the tests
    asyncio.run(run_native_tests())
'''
    
    with open("scripts/test_native.py", "w") as f:
        f.write(test_runner_code)
    
    # Make it executable
    os.chmod("scripts/test_native.py", 0o755)
    
    print("✅ Native test runner created (scripts/test_native.py)")
    return True

def print_instructions():
    """Print final instructions"""
    print_step(7, "Setup Complete! Next Steps")
    
    instructions = """
🎉 LOCAL SETUP COMPLETE! 

To test the repository locally (without Docker):

1. ACTIVATE VIRTUAL ENVIRONMENT:
   - On macOS/Linux: source venv/bin/activate
   - On Windows: venv\\Scripts\\activate

2. RUN NATIVE TESTS:
   python scripts/test_native.py

3. RUN UNIT TESTS:
   python -m pytest tests/ -v --tb=short

4. TEST INDIVIDUAL COMPONENTS:
   python -c "
   import asyncio
   from scripts.test_native import NativeQueryAgent
   
   async def test():
       agent = NativeQueryAgent()
       await agent.start()
       result = await agent.process_query('test_customer_12345', 'Test query')
       print(f'Result: {result}')
       await agent.stop()
   
   asyncio.run(test())
   "

5. VIEW LOGS:
   tail -f logs/native_test.log

CONFIGURATION FILES CREATED:
- .env.local (local settings)
- data/schema.sql (SQLite schema)
- scripts/test_native.py (test runner)

FEATURES AVAILABLE:
✅ SQLite database (no PostgreSQL needed)
✅ In-memory implementations (no Kafka/Redis needed)  
✅ MCP simulation (no Docker needed)
✅ A2A agent testing
✅ Full logging and debugging

OPTIONAL: Add your API keys to .env.local for LLM testing
    """
    
    print(instructions)

def main():
    """Main setup function"""
    print("🚀 Native Local Setup - No Docker Required")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup steps
    steps = [
        (setup_virtual_environment, "Setup virtual environment"),
        (install_dependencies, "Install dependencies"),
        (setup_local_database, "Setup local database"), 
        (create_local_config, "Create local config"),
        (setup_logging, "Setup logging"),
        (create_native_test_runner, "Create test runner")
    ]
    
    pip_path = None
    
    for i, (func, description) in enumerate(steps):
        try:
            if i == 0:  # First step returns pip_path
                pip_path = func()
                if not pip_path:
                    print(f"❌ Failed: {description}")
                    return False
            elif i == 1:  # Second step needs pip_path
                if not func(pip_path):
                    print(f"❌ Failed: {description}")
                    return False
            else:
                if not func():
                    print(f"❌ Failed: {description}")
                    return False
        except Exception as e:
            print(f"❌ Error in {description}: {e}")
            return False
    
    print_instructions()
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\\n✅ Setup completed successfully!")
'''
    
    with open("scripts/setup_native.py", "w") as f:
        f.write(setup_code)
    
    # Make it executable
    os.chmod("scripts/setup_native.py", 0o755)
    
    print("✅ Native setup script created")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
