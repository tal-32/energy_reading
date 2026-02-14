import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
STREAM_NAME = os.getenv("STREAM_NAME", "energy_readings")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "processing_group")
