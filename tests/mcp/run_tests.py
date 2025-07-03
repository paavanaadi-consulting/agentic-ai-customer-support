"""
MCP Test Suite Configuration and Runner
This module provides utilities for running the complete MCP test suite
"""
import pytest
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

def run_mcp_tests(verbose=True, coverage=True):
    """
    Run all MCP tests with optional coverage reporting
    
    Args:
        verbose (bool): Enable verbose output
        coverage (bool): Enable coverage reporting
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Base pytest arguments
    args = [
        str(Path(__file__).parent),  # Run tests in this directory
        "--tb=short",  # Short traceback format
        "-v" if verbose else "-q",  # Verbose or quiet mode
    ]
    
    # Add coverage arguments if requested
    if coverage:
        args.extend([
            "--cov=src.mcp",  # Coverage for MCP modules
            "--cov-report=html:test-results/mcp-coverage",  # HTML coverage report
            "--cov-report=term-missing",  # Terminal coverage with missing lines
            "--cov-fail-under=80",  # Fail if coverage below 80%
        ])
    
    # Run pytest
    return pytest.main(args)

def run_specific_test(test_module, test_function=None):
    """
    Run a specific test module or function
    
    Args:
        test_module (str): Name of the test module (e.g., 'test_mcp_client')
        test_function (str, optional): Specific test function to run
    
    Returns:
        int: Exit code
    """
    test_path = Path(__file__).parent / f"{test_module}.py"
    
    if not test_path.exists():
        print(f"Test module {test_module} not found")
        return 1
    
    args = [str(test_path), "-v"]
    
    if test_function:
        args.append(f"-k {test_function}")
    
    return pytest.main(args)

def list_available_tests():
    """List all available test modules in the MCP test suite"""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    print("Available MCP test modules:")
    for test_file in sorted(test_files):
        print(f"  - {test_file.stem}")
    
    return test_files

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MCP test suite")
    parser.add_argument("--module", help="Run specific test module")
    parser.add_argument("--function", help="Run specific test function")
    parser.add_argument("--list", action="store_true", help="List available test modules")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
        sys.exit(0)
    
    if args.module:
        exit_code = run_specific_test(args.module, args.function)
    else:
        exit_code = run_mcp_tests(
            verbose=not args.quiet,
            coverage=not args.no_coverage
        )
    
    sys.exit(exit_code)
