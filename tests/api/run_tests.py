#!/usr/bin/env python3
"""
Test runner for API module tests.
Provides comprehensive test execution with reporting and coverage.
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False, parallel=False):
    """
    Run API tests with various options.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, performance)
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Run tests in parallel
    """
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Test directory
    test_dir = Path(__file__).parent
    
    # Select test files based on type
    if test_type == "all":
        cmd.append(str(test_dir))
    elif test_type == "unit":
        cmd.extend([
            str(test_dir / "test_schemas.py"),
            str(test_dir / "test_routes.py"),
            str(test_dir / "test_dependencies.py"),
            str(test_dir / "test_api_main.py")
        ])
    elif test_type == "integration":
        cmd.append(str(test_dir / "test_integration.py"))
    elif test_type == "kafka":
        cmd.append(str(test_dir / "test_kafka_routes.py"))
    elif test_type == "performance":
        cmd.extend(["-m", "slow"])
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=src.api",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings"  # Disable warnings for cleaner output
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=test_dir.parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run API tests")
    
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "kafka", "performance"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()