import json
import logging
import os
import sys
from datetime import datetime, timezone

import redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
APP_NAME = os.getenv("APP_NAME", "cetuspro-devops-demo")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = FastAPI(title=APP_NAME)


def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=2)


@app.get("/", response_class=HTMLResponse)
def home():
    logger.info("Request received on /")
    try:
        r = get_redis()
        visits = r.incr("visits") 
    except redis.exceptions.RedisError:
        logger.error("Redis unavailable while handling /")
        visits = "N/A (Redis down)"
    return f"""
    <html>
      <body style="font-family: sans-serif; text-align: center; padding-top: 80px;">
        <h1>🐋 CetusPro — DevOps Task</h1>
        <p>Deploy &amp; Observe — recruitment task 2026</p>
        <p>Visits counter (stored in Redis): <b>{visits}</b></p>
        <p><a href="/health">/health</a></p>
      </body>
    </html>
    """


@app.get("/health")
def health():
    try:
        r = get_redis()
        r.ping()
        logger.info("Health check OK")
        return {"status": "ok", "redis": "connected"}
    except redis.exceptions.RedisError:
        logger.error("Health check FAILED: cannot reach Redis")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "redis": "unreachable"},
        )