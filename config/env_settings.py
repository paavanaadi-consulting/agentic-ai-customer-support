"""
Unified environment-specific settings loader for the project.
"""
import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Settings(BaseSettings):
    # AI Model API Keys
    CLAUDE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "admin"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "customer_support"

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPICS: str = "customer-queries,feedback-events"

    # Vector Database Configuration
    VECTOR_DB_HOST: str = "localhost"
    VECTOR_DB_PORT: int = 6333
    VECTOR_DB_COLLECTION: str = "knowledge_base"

    # Genetic Algorithm Settings
    POPULATION_SIZE: int = 20
    MUTATION_RATE: float = 0.1
    CROSSOVER_RATE: float = 0.8
    ELITE_SIZE: int = 4
    MAX_GENERATIONS: int = 100
    FITNESS_THRESHOLD: float = 0.95

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # AWS S3 Storage
    AWS_S3_BUCKET: str = "my-bucket"
    AWS_S3_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT_URL: str = "https://s3.amazonaws.com"

    # GCP Storage
    GCP_STORAGE_BUCKET: str = "my-gcp-bucket"
    GCP_STORAGE_PROJECT: str = "my-gcp-project"
    GCP_STORAGE_CREDENTIALS_PATH: str = "/path/to/gcp/credentials.json"

    # Azure Blob Storage
    AZURE_STORAGE_ACCOUNT: str = "myazureaccount"
    AZURE_STORAGE_KEY: str = "myazurekey"
    AZURE_STORAGE_CONTAINER: str = "mycontainer"
    AZURE_STORAGE_CONNECTION_STRING: str = "DefaultEndpointsProtocol=https;AccountName=myazureaccount;AccountKey=myazurekey;EndpointSuffix=core.windows.net"

    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class DevSettings(Settings):
    DEBUG: bool = True

class ProdSettings(Settings):
    DEBUG: bool = False

class TestSettings(Settings):
    DEBUG: bool = True

# Select settings class based on ENV
env = os.getenv("ENV", "development").lower()
if env == "production":
    EnvSettings = ProdSettings
elif env == "test":
    EnvSettings = TestSettings
else:
    EnvSettings = DevSettings

env_settings = EnvSettings()
