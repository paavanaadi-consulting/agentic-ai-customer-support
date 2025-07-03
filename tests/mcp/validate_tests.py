#!/usr/bin/env python3
"""
MCP Test Suite Validation Script
Validates test coverage and completeness for all MCP modules
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Set

def get_source_modules() -> Set[str]:
    """Get all Python modules in src/mcp directory"""
    src_mcp_path = Path(__file__).parent.parent.parent / "src" / "mcp"
    
    if not src_mcp_path.exists():
        print(f"Error: Source MCP directory not found: {src_mcp_path}")
        return set()
    
    modules = set()
    for py_file in src_mcp_path.glob("*.py"):
        if py_file.name != "__init__.py":
            modules.add(py_file.stem)
    
    return modules

def get_test_modules() -> Set[str]:
    """Get all test modules in tests/mcp directory"""
    test_mcp_path = Path(__file__).parent
    
    modules = set()
    for py_file in test_mcp_path.glob("test_*.py"):
        # Extract source module name from test file name
        # test_mcp_client.py -> mcp_client
        module_name = py_file.name[5:-3]  # Remove 'test_' prefix and '.py' suffix
        modules.add(module_name)
    
    return modules

def check_test_coverage() -> Dict[str, str]:
    """Check which source modules have corresponding test files"""
    source_modules = get_source_modules()
    test_modules = get_test_modules()
    
    coverage_status = {}
    
    for module in source_modules:
        if module in test_modules:
            coverage_status[module] = "✓ Covered"
        else:
            coverage_status[module] = "✗ Missing test"
    
    # Check for orphaned test files
    for test_module in test_modules:
        if test_module not in source_modules:
            coverage_status[f"test_{test_module}"] = "⚠ Orphaned test (no source)"
    
    return coverage_status

def analyze_test_file_completeness(test_file: Path) -> Dict[str, any]:
    """Analyze a test file for completeness"""
    try:
        content = test_file.read_text()
        
        analysis = {
            "file": test_file.name,
            "has_imports": "import pytest" in content or "from pytest" in content,
            "has_asyncio": "pytest.mark.asyncio" in content or "@pytest.mark.asyncio" in content,
            "has_fixtures": "@pytest.fixture" in content,
            "has_mocks": "mock" in content.lower() or "Mock" in content,
            "has_docstrings": '"""' in content,
            "test_classes": content.count("class Test"),
            "test_methods": content.count("def test_"),
            "async_tests": content.count("async def test_"),
            "line_count": len(content.splitlines()),
        }
        
        return analysis
    except Exception as e:
        return {"file": test_file.name, "error": str(e)}

def validate_test_structure() -> List[Dict]:
    """Validate the structure and completeness of test files"""
    test_mcp_path = Path(__file__).parent
    test_files = list(test_mcp_path.glob("test_*.py"))
    
    analyses = []
    for test_file in test_files:
        analysis = analyze_test_file_completeness(test_file)
        analyses.append(analysis)
    
    return analyses

def check_required_files() -> Dict[str, bool]:
    """Check for required test infrastructure files"""
    test_mcp_path = Path(__file__).parent
    
    required_files = {
        "__init__.py": "Test package marker",
        "README.md": "Test documentation",
        "run_tests.py": "Test runner script",
        "pyproject.toml": "Pytest configuration",
    }
    
    file_status = {}
    for filename, description in required_files.items():
        file_path = test_mcp_path / filename
        file_status[f"{filename} ({description})"] = file_path.exists()
    
    return file_status

def print_coverage_report():
    """Print comprehensive test coverage report"""
    print("=" * 80)
    print("MCP TEST SUITE VALIDATION REPORT")
    print("=" * 80)
    
    # Test coverage analysis
    print("\n📊 TEST COVERAGE ANALYSIS")
    print("-" * 40)
    coverage_status = check_test_coverage()
    
    covered_count = sum(1 for status in coverage_status.values() if status.startswith("✓"))
    total_count = len([k for k in coverage_status.keys() if not k.startswith("test_")])
    
    for module, status in sorted(coverage_status.items()):
        print(f"{module:25} {status}")
    
    print(f"\nCoverage: {covered_count}/{total_count} modules ({covered_count/total_count*100:.1f}%)")
    
    # Test file structure analysis
    print("\n📋 TEST FILE ANALYSIS")
    print("-" * 40)
    analyses = validate_test_structure()
    
    total_test_classes = 0
    total_test_methods = 0
    total_async_tests = 0
    total_lines = 0
    
    for analysis in analyses:
        if "error" in analysis:
            print(f"❌ {analysis['file']}: {analysis['error']}")
            continue
        
        file_name = analysis['file']
        classes = analysis['test_classes']
        methods = analysis['test_methods']
        async_tests = analysis['async_tests']
        lines = analysis['line_count']
        
        total_test_classes += classes
        total_test_methods += methods
        total_async_tests += async_tests
        total_lines += lines
        
        # Quality indicators
        indicators = []
        if analysis['has_fixtures']:
            indicators.append("fixtures")
        if analysis['has_mocks']:
            indicators.append("mocks")
        if analysis['has_asyncio']:
            indicators.append("async")
        if analysis['has_docstrings']:
            indicators.append("docs")
        
        quality_str = ", ".join(indicators) if indicators else "basic"
        
        print(f"{file_name:30} {classes:2}cls {methods:3}tests {async_tests:2}async {lines:4}lines [{quality_str}]")
    
    print(f"\nTotal: {total_test_classes} test classes, {total_test_methods} test methods")
    print(f"Async tests: {total_async_tests}/{total_test_methods} ({total_async_tests/total_test_methods*100:.1f}%)")
    print(f"Total lines: {total_lines:,}")
    
    # Infrastructure files check
    print("\n🔧 INFRASTRUCTURE FILES")
    print("-" * 40)
    file_status = check_required_files()
    
    for filename, exists in file_status.items():
        status = "✓" if exists else "✗"
        print(f"{status} {filename}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    
    missing_tests = [module for module, status in coverage_status.items() 
                    if status.startswith("✗")]
    
    if missing_tests:
        print("⚠️  Missing test files for:")
        for module in missing_tests:
            print(f"   - {module}")
        print()
    
    # Quality recommendations
    for analysis in analyses:
        if "error" in analysis:
            continue
            
        file_name = analysis['file']
        recommendations = []
        
        if not analysis['has_fixtures']:
            recommendations.append("add pytest fixtures")
        if not analysis['has_mocks']:
            recommendations.append("add mocking for external dependencies")
        if analysis['test_methods'] < 5:
            recommendations.append("consider adding more test cases")
        if analysis['async_tests'] == 0 and "async" in file_name:
            recommendations.append("add async test cases for async functionality")
        
        if recommendations:
            print(f"📝 {file_name}: {', '.join(recommendations)}")
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

def main():
    """Main function"""
    try:
        print_coverage_report()
        
        # Exit with error code if coverage is incomplete
        coverage_status = check_test_coverage()
        missing_tests = [module for module, status in coverage_status.items() 
                        if status.startswith("✗")]
        
        if missing_tests:
            print(f"\n❌ Validation failed: {len(missing_tests)} modules without tests")
            return 1
        else:
            print("\n✅ Validation passed: All modules have test coverage")
            return 0
            
    except Exception as e:
        print(f"Error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
