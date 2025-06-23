# Local Testing Troubleshooting Guide

This guide helps you resolve common issues when testing the repository locally without Docker.

## Quick Diagnostics

### 1. Check Your Setup
```bash
# Verify Python version (should be 3.11+)
python3 --version

# Check if virtual environment is active
which python
# Should show: /Users/your-username/.../venv/bin/python

# Verify required packages are installed
pip list | grep -E "(fastapi|sqlite|asyncio|pytest)"

# Check database exists
ls -la data/test.db
```

### 2. Check File Permissions
```bash
# Make sure scripts are executable
chmod +x start_local_testing.sh
chmod +x scripts/test_native.py
chmod +x scripts/setup_native.py

# Check directory permissions
ls -la data/ logs/
```

## Common Issues and Solutions

### Issue 1: "ModuleNotFoundError" or Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: No module named 'sqlite3'
```

**Solutions:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue 2: "Permission denied" or "File not found"

**Symptoms:**
```
bash: ./start_local_testing.sh: Permission denied
FileNotFoundError: [Errno 2] No such file or directory: 'data/test.db'
```

**Solutions:**
```bash
# Fix script permissions
chmod +x start_local_testing.sh
chmod +x scripts/*.py

# Create missing directories
mkdir -p data logs

# Run setup script
python scripts/setup_native.py
```

### Issue 3: SQLite Database Issues

**Symptoms:**
```
sqlite3.OperationalError: no such table: customers
sqlite3.OperationalError: database is locked
```

**Solutions:**
```bash
# Remove and recreate database
rm -f data/test.db

# Run database setup
python -c "
import sqlite3
conn = sqlite3.connect('data/test.db')
# ... (database creation code from start_local_testing.sh)
"

# Or use the setup script
python scripts/setup_native.py
```

### Issue 4: Port Already in Use

**Symptoms:**
```
OSError: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Check what's using the ports
lsof -i :8101
lsof -i :8102
lsof -i :8103

# Kill processes using those ports
kill -9 <PID>

# Or use different ports by editing .env.local
nano .env.local
# Change A2A_*_PORT values
```

### Issue 5: Test Failures

**Symptoms:**
```
AssertionError: Test failed
RuntimeError: Agent not running
```

**Solutions:**
```bash
# Run tests with verbose output
python scripts/test_native.py --verbose

# Check detailed logs
tail -f logs/native_test.log

# Run individual test components
python scripts/test_native.py --scenario basic
python scripts/test_native.py --scenario knowledge
python scripts/test_native.py --scenario response
```

### Issue 6: Virtual Environment Issues

**Symptoms:**
```
Command 'python' not found
pip: command not found
```

**Solutions:**
```bash
# Create new virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# On some systems, use python instead of python3
python --version
# If this shows Python 3.11+, use 'python' instead of 'python3'
```

### Issue 7: macOS Specific Issues

**Symptoms:**
```
xcrun: error: invalid active developer path
```

**Solutions:**
```bash
# Install Xcode command line tools
xcode-select --install

# If using Homebrew Python
brew install python@3.11
```

## Environment Variables Issues

### Check Current Environment
```bash
# Print all environment variables
env | grep -E "(DATABASE|KAFKA|MCP|A2A)"

# Check if .env.local is being loaded
python -c "
import os
from pathlib import Path
if os.path.exists('.env.local'):
    print('✅ .env.local exists')
    with open('.env.local') as f:
        print(f.read())
else:
    print('❌ .env.local not found')
"
```

### Reset Environment Configuration
```bash
# Backup existing config
cp .env.local .env.local.backup

# Reset to defaults
cp .env.native .env.local

# Or manually create minimal config
cat > .env.local << EOF
DATABASE_URL=sqlite:///./data/test.db
TEST_MODE=native
NATIVE_TESTING=true
LOG_LEVEL=INFO
EOF
```

## Performance Issues

### Slow Test Execution
```bash
# Run performance diagnostics
python scripts/test_native.py --scenario performance

# Check system resources
top -o cpu
df -h  # Check disk space
```

### Memory Issues
```bash
# Monitor memory usage during tests
python -c "
import asyncio
import psutil
import sys
sys.path.append('.')
from scripts.test_native import test_full_pipeline

async def monitor_test():
    process = psutil.Process()
    print(f'Memory before: {process.memory_info().rss / 1024 / 1024:.1f}MB')
    await test_full_pipeline()
    print(f'Memory after: {process.memory_info().rss / 1024 / 1024:.1f}MB')

asyncio.run(monitor_test())
"
```

## Advanced Debugging

### Enable Debug Logging
```bash
# Run with maximum verbosity
python scripts/test_native.py --verbose

# Or set log level in environment
export LOG_LEVEL=DEBUG
python scripts/test_native.py
```

### Inspect Database Contents
```bash
# Connect to SQLite database
sqlite3 data/test.db

# List all tables
.tables

# Check customer data
SELECT * FROM customers;

# Check knowledge articles
SELECT * FROM knowledge_articles;

# Exit SQLite
.quit
```

### Test Individual Components
```bash
# Test MCP client
python -c "
import asyncio
import sys
sys.path.append('.')
from scripts.test_native import NativeMockMCPClient

async def test():
    client = NativeMockMCPClient()
    await client.start()
    result = await client.call_tool('database', 'query_customers', {})
    print(f'Database test: {result}')
    await client.stop()

asyncio.run(test())
"

# Test individual agents
python -c "
import asyncio
import sys
sys.path.append('.')
from scripts.test_native import NativeQueryAgent

async def test():
    agent = NativeQueryAgent()
    await agent.start()
    result = await agent.process_query('test_customer_12345', 'test query')
    print(f'Agent test: {result}')
    await agent.stop()

asyncio.run(test())
"
```

## Getting Help

### Collect Diagnostic Information
```bash
# Create a diagnostic report
echo "=== System Information ===" > debug_report.txt
uname -a >> debug_report.txt
python3 --version >> debug_report.txt
echo "" >> debug_report.txt

echo "=== Python Environment ===" >> debug_report.txt
which python >> debug_report.txt
pip list >> debug_report.txt
echo "" >> debug_report.txt

echo "=== File Structure ===" >> debug_report.txt
ls -la >> debug_report.txt
ls -la data/ >> debug_report.txt
ls -la logs/ >> debug_report.txt
echo "" >> debug_report.txt

echo "=== Configuration ===" >> debug_report.txt
cat .env.local >> debug_report.txt
echo "" >> debug_report.txt

echo "=== Recent Logs ===" >> debug_report.txt
tail -50 logs/native_test.log >> debug_report.txt

echo "Diagnostic report created: debug_report.txt"
```

### Clean Reset
```bash
# Complete clean reset (CAUTION: This removes all local data)
rm -rf venv data logs .env.local
rm -f debug_report.txt

# Start fresh
./start_local_testing.sh
```

## Success Checklist

After resolving issues, verify everything works:

- [ ] Virtual environment is active
- [ ] All dependencies are installed
- [ ] SQLite database exists with sample data
- [ ] Configuration files are present
- [ ] Scripts are executable
- [ ] Basic test passes: `python scripts/test_native.py --scenario basic`
- [ ] Full test passes: `python scripts/test_native.py --scenario full`
- [ ] Unit tests pass: `python -m pytest tests/ -v`
- [ ] Log files are being created in `logs/`

If all items are checked, your local testing environment is working correctly! 🎉
