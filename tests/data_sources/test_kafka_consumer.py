from data_sources.kafka_consumer import KafkaConsumer
import pytest

@pytest.mark.asyncio
async def test_kafka_consumer_start():
    consumer = KafkaConsumer({"bootstrap_servers": "localhost:9092", "topics": ["test"]})
    await consumer.start()
    assert hasattr(consumer, 'start')
