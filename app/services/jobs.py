import json
import logging
import uuid
from typing import Dict, Any, Optional
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory job store if Redis is unavailable or during local offline dev
_MEMORY_JOBS: Dict[str, Dict[str, Any]] = {}

_redis_client: Optional[redis.Redis] = None
_redis_initialized = False

def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client, _redis_initialized
    if not _redis_initialized:
        _redis_initialized = True
        try:
            if settings.REDIS_URL:
                client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
                client.ping()
                _redis_client = client
                logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to memory store.")
            _redis_client = None
    return _redis_client

class JobService:
    @staticmethod
    def create_job() -> str:
        job_id = str(uuid.uuid4())
        initial_data = {"job_id": job_id, "status": "queued"}
        client = get_redis_client()
        if client:
            try:
                client.set(f"job:{job_id}", json.dumps(initial_data), ex=86400)
                return job_id
            except Exception as e:
                logger.warning(f"Error setting job in Redis: {e}")
        _MEMORY_JOBS[job_id] = initial_data
        return job_id

    @staticmethod
    def update_job(job_id: str, status: str, result: dict = None) -> None:
        client = get_redis_client()
        if client:
            try:
                val = client.get(f"job:{job_id}")
                if val:
                    data = json.loads(val)
                else:
                    data = {"job_id": job_id}
                data["status"] = status
                if result:
                    data["result"] = result
                client.set(f"job:{job_id}", json.dumps(data), ex=86400)
                return
            except Exception as e:
                logger.warning(f"Error updating job in Redis: {e}")
                
        if job_id in _MEMORY_JOBS:
            _MEMORY_JOBS[job_id]["status"] = status
            if result:
                _MEMORY_JOBS[job_id]["result"] = result

    @staticmethod
    def get_job(job_id: str) -> Optional[dict]:
        client = get_redis_client()
        if client:
            try:
                val = client.get(f"job:{job_id}")
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Error retrieving job from Redis: {e}")
        return _MEMORY_JOBS.get(job_id)

