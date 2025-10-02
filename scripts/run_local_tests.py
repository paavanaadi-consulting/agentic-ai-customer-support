#!/usr/bin/env python3
"""
Simple test runner for local development
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Local test runner for the application"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {}
        
    def run_command(self, command: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run a command and return results"""
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            execution_time = time.time() - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'execution_time': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0
            }
    
    def test_python_imports(self) -> Dict[str, Any]:
        """Test that all required modules can be imported"""
        print("🔍 Testing Python imports...")
        
        imports_to_test = [
            "import psycopg2",
            "import kafka",
            "import qdrant_client",
            "import fastapi",
            "import anthropic",
            "import openai",
            "from src.utils.logger import setup_logger",
            "from src.api.api_main import app",
            "from config.settings import CONFIG"
        ]
        
        results = {}
        for import_stmt in imports_to_test:
            result = self.run_command(['python3', '-c', import_stmt], timeout=10)
            module_name = import_stmt.split()[-1].replace('from ', '').replace(' import', '')
            results[module_name] = result['success']
            
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {module_name}")
            
            if not result['success']:
                print(f"    Error: {result['stderr']}")
        
        return results
    
    def test_database_scripts(self) -> Dict[str, Any]:
        """Test database-related scripts"""
        print("\n🗄️  Testing database scripts...")
        
        scripts = [
            ('test_postgresql.py', 'PostgreSQL connectivity'),
            ('init_db.py', 'Database initialization'),
            ('seed_db.py', 'Database seeding')
        ]
        
        results = {}
        for script, description in scripts:
            script_path = self.project_root / 'scripts' / script
            if script_path.exists():
                print(f"  Testing {description}...")
                result = self.run_command(['python3', str(script_path)], timeout=30)
                results[script] = result['success']
                
                status = "✅" if result['success'] else "❌"
                print(f"    {status} {script}")
                
                if not result['success']:
                    print(f"    Error: {result['stderr'][:200]}")
            else:
                results[script] = False
                print(f"    ❌ {script} (not found)")
        
        return results
    
    def test_api_scripts(self) -> Dict[str, Any]:
        """Test API-related scripts"""
        print("\n🌐 Testing API scripts...")
        
        scripts = [
            ('test_api.py', 'API functionality'),
            ('test_api_integration.py', 'API integration')
        ]
        
        results = {}
        for script, description in scripts:
            script_path = self.project_root / 'scripts' / script
            if script_path.exists():
                print(f"  Testing {description}...")
                result = self.run_command(['python3', str(script_path)], timeout=30)
                results[script] = result['success']
                
                status = "✅" if result['success'] else "❌"
                print(f"    {status} {script}")
                
                if not result['success']:
                    print(f"    Error: {result['stderr'][:200]}")
            else:
                results[script] = False
                print(f"    ❌ {script} (not found)")
        
        return results
    
    def test_mcp_scripts(self) -> Dict[str, Any]:
        """Test MCP-related scripts"""
        print("\n🔌 Testing MCP scripts...")
        
        scripts = [
            ('test_mcp_postgres.py', 'PostgreSQL MCP'),
            ('test_kafka.py', 'Kafka connectivity'),
            ('test_aws_mcp.py', 'AWS MCP')
        ]
        
        results = {}
        for script, description in scripts:
            script_path = self.project_root / 'scripts' / script
            if script_path.exists():
                print(f"  Testing {description}...")
                result = self.run_command(['python3', str(script_path)], timeout=30)
                results[script] = result['success']
                
                status = "✅" if result['success'] else "❌"
                print(f"    {status} {script}")
                
                if not result['success']:
                    print(f"    Error: {result['stderr'][:200]}")
            else:
                results[script] = False
                print(f"    ❌ {script} (not found)")
        
        return results
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test configuration files"""
        print("\n⚙️  Testing configuration...")
        
        config_files = [
            'config/settings.py',
            'config/env_settings.py',
            'pyproject.toml',
            'setup.py'
        ]
        
        results = {}
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                results[config_file] = True
                print(f"  ✅ {config_file}")
            else:
                results[config_file] = False
                print(f"  ❌ {config_file} (missing)")
        
        # Test settings import
        try:
            from config.settings import CONFIG
            results['settings_import'] = True
            print("  ✅ Settings import successful")
        except Exception as e:
            results['settings_import'] = False
            print(f"  ❌ Settings import failed: {str(e)}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        print("🧪 Running Local Development Tests")
        print("=" * 50)
        
        all_results = {}
        
        # Test imports
        all_results['imports'] = self.test_python_imports()
        
        # Test configuration
        all_results['configuration'] = self.test_configuration()
        
        # Test database scripts
        all_results['database'] = self.test_database_scripts()
        
        # Test MCP scripts
        all_results['mcp'] = self.test_mcp_scripts()
        
        # Test API scripts
        all_results['api'] = self.test_api_scripts()
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 Test Summary:")
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in all_results.items():
            category_passed = sum(tests.values())
            category_total = len(tests)
            total_tests += category_total
            passed_tests += category_passed
            
            status = "✅" if category_passed == category_total else "⚠️"
            print(f"  {status} {category.title()}: {category_passed}/{category_total}")
        
        print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("✅ All tests passed! System ready for development.")
        else:
            print("⚠️  Some tests failed. Check individual test outputs above.")
        
        return {
            'summary': {
                'passed': passed_tests,
                'total': total_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            },
            'details': all_results
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local test runner for Agentic AI Customer Support')
    parser.add_argument('--category', choices=['imports', 'config', 'database', 'mcp', 'api'], 
                       help='Run tests for specific category only')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.category:
        # Run specific category
        if args.category == 'imports':
            results = runner.test_python_imports()
        elif args.category == 'config':
            results = runner.test_configuration()
        elif args.category == 'database':
            results = runner.test_database_scripts()
        elif args.category == 'mcp':
            results = runner.test_mcp_scripts()
        elif args.category == 'api':
            results = runner.test_api_scripts()
        
        if args.json:
            print(json.dumps(results, indent=2))
    else:
        # Run all tests
        results = runner.run_all_tests()
        
        if args.json:
            print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        success_rate = results['summary']['success_rate']
        sys.exit(0 if success_rate == 1.0 else 1)

if __name__ == "__main__":
    main()
