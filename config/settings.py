"""
Project-wide configuration loader for all services, including MCP connectors.
"""
from config.env_settings import env_settings

CONFIG = {
    # AI Model API Keys
    "ai_models": {
        "claude_api_key": env_settings.CLAUDE_API_KEY,
        "gemini_api_key": env_settings.GEMINI_API_KEY,
        "openai_api_key": env_settings.OPENAI_API_KEY,
    },
    # Database
    "vector_db": {
        "host": env_settings.VECTOR_DB_HOST,
        "port": env_settings.VECTOR_DB_PORT,
        "collection": env_settings.VECTOR_DB_COLLECTION,
    },
    "kafka": {
        "bootstrap_servers": env_settings.KAFKA_BOOTSTRAP_SERVERS,
        "topics": env_settings.KAFKA_TOPICS.split(","),
    },
    "genetic": {
        "population_size": env_settings.POPULATION_SIZE,
        "mutation_rate": env_settings.MUTATION_RATE,
        "crossover_rate": env_settings.CROSSOVER_RATE,
        "elite_size": env_settings.ELITE_SIZE,
        "max_generations": env_settings.MAX_GENERATIONS,
        "fitness_threshold": env_settings.FITNESS_THRESHOLD,
    },
    # MCP Connectors
    "mcp_postgres": {
        "host": env_settings.DB_HOST,
        "port": env_settings.DB_PORT,
        "user": env_settings.DB_USER,
        "password": env_settings.DB_PASSWORD,
        "dbname": env_settings.DB_NAME,
    },
    "mcp_kafka": {
        "bootstrap_servers": env_settings.KAFKA_BOOTSTRAP_SERVERS,
        "topics": env_settings.KAFKA_TOPICS.split(","),
    },
    "mcp_aws": {
        "aws_access_key_id": getattr(env_settings, "AWS_ACCESS_KEY_ID", None),
        "aws_secret_access_key": getattr(env_settings, "AWS_SECRET_ACCESS_KEY", None),
        "region_name": env_settings.AWS_S3_REGION,
        # Add more AWS config as needed
    },
    "mcp_aws_external": {
        "access_key": getattr(env_settings, "AWS_ACCESS_KEY_ID", None),
        "secret_key": getattr(env_settings, "AWS_SECRET_ACCESS_KEY", None),
        "region": env_settings.AWS_S3_REGION,
        "use_external_servers": True,
        "service_types": ["lambda", "sns", "sqs", "mq"],
        "timeout": 30,
        "max_retries": 3,
        # Lambda configuration
        "lambda": {
            "default_function": getattr(env_settings, "AWS_DEFAULT_LAMBDA", None)
        },
        # SNS configuration
        "sns": {
            "default_topic": getattr(env_settings, "AWS_DEFAULT_SNS_TOPIC", None)
        },
        # SQS configuration
        "sqs": {
            "default_queue": getattr(env_settings, "AWS_DEFAULT_SQS_QUEUE", None)
        },
        # MQ configuration
        "mq": {
            "default_broker": getattr(env_settings, "AWS_DEFAULT_MQ_BROKER", None)
        }
    },
}
