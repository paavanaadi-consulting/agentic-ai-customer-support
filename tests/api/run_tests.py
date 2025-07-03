"""
Test runner for API tests.
Can be run with or without pytest installed.
"""
import sys
import os
import importlib.util

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def run_tests_without_pytest():
    """Run tests without pytest dependency"""
    print("Running API tests without pytest...")
    
    try:
        # Import and run integration tests
        from test_integration import (
            TestAPIIntegration, TestAPIDocumentation, 
            TestAPIPerformance, TestAPIErrorHandling
        )
        
        # Run basic integration tests
        print("\n=== API Integration Tests ===")
        test_integration = TestAPIIntegration()
        test_integration.setup_method()
        test_integration.test_health_endpoint()
        test_integration.test_api_routes_available()
        test_integration.test_cors_headers()
        print("✓ API Integration tests passed")
        
        # Run documentation tests
        print("\n=== API Documentation Tests ===")
        test_docs = TestAPIDocumentation()
        test_docs.setup_method()
        test_docs.test_openapi_schema()
        test_docs.test_docs_endpoint()
        test_docs.test_redoc_endpoint()
        print("✓ API Documentation tests passed")
        
        # Run performance tests
        print("\n=== API Performance Tests ===")
        test_performance = TestAPIPerformance()
        test_performance.setup_method()
        test_performance.test_response_time_reasonable()
        test_performance.test_concurrent_requests()
        print("✓ API Performance tests passed")
        
        # Run error handling tests
        print("\n=== API Error Handling Tests ===")
        test_errors = TestAPIErrorHandling()
        test_errors.setup_method()
        test_errors.test_404_handling()
        test_errors.test_method_not_allowed()
        test_errors.test_invalid_json()
        print("✓ API Error Handling tests passed")
        
        print("\n🎉 All API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_tests_with_pytest():
    """Run tests with pytest if available"""
    try:
        import pytest
        print("Running API tests with pytest...")
        
        # Run pytest on the current directory
        test_dir = os.path.dirname(__file__)
        exit_code = pytest.main([
            test_dir,
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
        
        if exit_code == 0:
            print("🎉 All pytest tests completed successfully!")
            return True
        else:
            print(f"❌ Some pytest tests failed (exit code: {exit_code})")
            return False
            
    except ImportError:
        print("pytest not available, falling back to basic test runner")
        return run_tests_without_pytest()


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    # Check for FastAPI
    try:
        import fastapi
        print(f"✓ FastAPI {fastapi.__version__} available")
    except ImportError:
        missing_deps.append("fastapi")
    
    # Check for Pydantic
    try:
        import pydantic
        print(f"✓ Pydantic {pydantic.__version__} available")
    except ImportError:
        missing_deps.append("pydantic")
    
    # Check for pytest (optional)
    try:
        import pytest
        print(f"✓ pytest {pytest.__version__} available")
    except ImportError:
        print("⚠ pytest not available (will use basic test runner)")
    
    if missing_deps:
        print(f"❌ Missing required dependencies: {', '.join(missing_deps)}")
        print("Please install missing dependencies with:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True


def main():
    """Main test runner"""
    print("API Test Runner")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\nStarting API tests...")
    
    # Try pytest first, fall back to basic runner
    try:
        success = run_tests_with_pytest()
    except Exception as e:
        print(f"Error running pytest: {e}")
        success = run_tests_without_pytest()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
