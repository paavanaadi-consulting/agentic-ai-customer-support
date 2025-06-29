from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentic-ai-customer-support",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A genetic AI system for customer support using multiple AI agents with external MCP server integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentic-ai-customer-support",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core AI model dependencies
        "anthropic>=0.25.0",
        "google-generativeai>=0.3.0",
        "openai>=1.0.0",
        
        # Database dependencies
        "psycopg2-binary>=2.9.0",
        
        # Vector database and ML
        "qdrant-client>=1.6.0",
        "sentence-transformers>=2.2.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        
        # PDF processing
        "PyPDF2>=3.0.0",
        
        # Web framework
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        
        # Environment and configuration
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "mcp": [
            # MCP communication dependencies
            "websockets>=11.0.0",
        ],
        "kafka-fallback": [
            # Only needed if using custom Kafka MCP fallback
            "kafka-python>=2.0.0",
        ],
        "aws-fallback": [
            # Only needed if using custom AWS MCP fallback
            "boto3>=1.26.0",
        ],
        "server": [
            # Web server dependencies
            "uvicorn>=0.20.0",
            "python-multipart>=0.0.6",
        ],
        "visualization": [
            # Data visualization dependencies
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
        ],
        "logging": [
            # Enhanced logging
            "loguru>=0.7.0",
        ],
        "all": [
            # Install all optional dependencies
            "websockets>=11.0.0",
            "kafka-python>=2.0.0",
            "boto3>=1.26.0",
            "uvicorn>=0.20.0",
            "python-multipart>=0.0.6",
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "loguru>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "genetic-ai-support=main:main",
        ],
    },
)
