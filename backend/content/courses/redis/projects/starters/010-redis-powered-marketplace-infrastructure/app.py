"""Starter for a Redis learning project. Not a production-ready service."""
import os
import redis


def create_client():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)


def main():
    client = create_client()
    try:
        print("Redis reachable:", client.ping())
        # TODO: implement the project requirement with demo: keys and synthetic records.
        # TODO: test timeout, missing key, repeated request and cleanup behavior.
    finally:
        client.close()


if __name__ == "__main__":
    main()
