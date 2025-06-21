"""
Health check script for core services.
"""
import socket
from config.settings import settings

def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, int(port)))
        s.close()
        return True
    except Exception:
        return False

def main():
    print("Vector DB:", "UP" if check_port(settings.VECTOR_DB_HOST, settings.VECTOR_DB_PORT) else "DOWN")
    print("Postgres:", "UP" if check_port(settings.DB_HOST, settings.DB_PORT) else "DOWN")
    print("Kafka:", "UP" if check_port(settings.KAFKA_BOOTSTRAP_SERVERS.split(':')[0], settings.KAFKA_BOOTSTRAP_SERVERS.split(':')[1]) else "DOWN")

if __name__ == "__main__":
    main()
