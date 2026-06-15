import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from redis import Redis
from redis.exceptions import RedisError


app = Flask(__name__)


def redis_client() -> Redis:
    password = os.getenv("REDIS_PASSWORD") or None
    return Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=password,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


@app.get("/api/ping")
def ping():
    app.logger.info("received /api/ping from %s", request.remote_addr)
    return jsonify(
        {
            "status": "ok",
            "service": "cloud-course-backend",
            "time": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.get("/api/redis")
def read_redis_value():
    key = request.args.get("key", "testkey")
    try:
        value = redis_client().get(key)
    except RedisError as exc:
        app.logger.exception("redis read failed")
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({"status": "ok", "key": key, "value": value})


@app.post("/api/redis")
def write_redis_value():
    payload = request.get_json(silent=True) or {}
    key = payload.get("key", "testkey")
    value = payload.get("value", "hello")

    try:
        redis_client().set(key, value)
    except RedisError as exc:
        app.logger.exception("redis write failed")
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({"status": "ok", "key": key, "value": value})


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
    )
