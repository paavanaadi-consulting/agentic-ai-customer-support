from mcp_servers.kafka_mcp import KafkaMCP

def test_kafka_mcp_methods():
    mcp = KafkaMCP({"bootstrap_servers": "localhost:9092"})
    # These methods are stubs, just check they run
    mcp.connect()
    mcp.send("test")
    mcp.receive()
    mcp.close()
