from __future__ import annotations

import json
import logging
import os
import socket
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field


APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_FILE = DATA_DIR / "items.json"

AWS_METADATA_BASE = "http://169.254.169.254"
METADATA_TOKEN_URL = f"{AWS_METADATA_BASE}/latest/api/token"
INSTANCE_ID_URL = f"{AWS_METADATA_BASE}/latest/meta-data/instance-id"
AZ_URL = f"{AWS_METADATA_BASE}/latest/meta-data/placement/availability-zone"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "hostname": socket.gethostname(),
        }

        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id

        if hasattr(record, "method"):
            payload["method"] = record.method

        if hasattr(record, "path"):
            payload["path"] = record.path

        if hasattr(record, "status_code"):
            payload["status_code"] = record.status_code

        if hasattr(record, "latency_ms"):
            payload["latency_ms"] = record.latency_ms

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


logger = logging.getLogger("platform-demo")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False


# ---------------------------------------------------------------------------
# Application models
# ---------------------------------------------------------------------------

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    status: str = Field(default="healthy", min_length=1, max_length=50)


class Item(BaseModel):
    id: int
    name: str
    status: str


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def ensure_data_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_items() -> list[dict[str, Any]]:
    ensure_data_store()

    try:
        contents = DATA_FILE.read_text(encoding="utf-8")
        data = json.loads(contents)

        if not isinstance(data, list):
            raise ValueError("Data file must contain a JSON array")

        return data

    except (OSError, json.JSONDecodeError, ValueError):
        logger.exception("failed_to_load_items")
        raise


def save_items(items: list[dict[str, Any]]) -> None:
    ensure_data_store()

    temporary_file = DATA_FILE.with_suffix(".tmp")

    try:
        temporary_file.write_text(
            json.dumps(items, indent=2),
            encoding="utf-8",
        )
        temporary_file.replace(DATA_FILE)

    except OSError:
        logger.exception("failed_to_save_items")
        raise


# ---------------------------------------------------------------------------
# EC2 metadata
# ---------------------------------------------------------------------------

def get_instance_metadata() -> dict[str, str | None]:
    """
    Query EC2 Instance Metadata Service v2.

    Outside EC2, or when IMDS is unavailable, return None values.
    This keeps the application runnable locally.
    """

    metadata: dict[str, str | None] = {
        "instance_id": None,
        "availability_zone": None,
    }

    try:
        with httpx.Client(timeout=1.0) as client:
            token_response = client.put(
                METADATA_TOKEN_URL,
                headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            )

            token_response.raise_for_status()
            token = token_response.text

            headers = {
                "X-aws-ec2-metadata-token": token,
            }

            instance_response = client.get(
                INSTANCE_ID_URL,
                headers=headers,
            )
            az_response = client.get(
                AZ_URL,
                headers=headers,
            )

            if instance_response.is_success:
                metadata["instance_id"] = instance_response.text

            if az_response.is_success:
                metadata["availability_zone"] = az_response.text

    except (httpx.HTTPError, OSError):
        logger.debug("ec2_metadata_unavailable")

    return metadata


# ---------------------------------------------------------------------------
# FastAPI lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "application_starting",
        extra={
            "request_id": "startup",
        },
    )

    ensure_data_store()

    yield

    logger.info(
        "application_stopping",
        extra={
            "request_id": "shutdown",
        },
    )


app = FastAPI(
    title="Platform Demo",
    version=APP_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    try:
        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "latency_ms": latency_ms,
            },
        )

        raise


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    """
    Basic liveness check.

    Initially this only tells us that the application process is alive.
    Later we can evolve this into a readiness/dependency check.
    """
    return {"status": "healthy"}


@app.get("/info")
def info() -> dict[str, Any]:
    metadata = get_instance_metadata()

    return {
        "hostname": socket.gethostname(),
        "instance_id": metadata["instance_id"],
        "availability_zone": metadata["availability_zone"],
        "version": APP_VERSION,
    }


@app.get("/api/items", response_model=list[Item])
def get_items() -> list[dict[str, Any]]:
    return load_items()


@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> dict[str, Any]:
    items = load_items()

    for item in items:
        if item["id"] == item_id:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Item {item_id} not found",
    )


@app.post(
    "/api/items",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
)
def create_item(item: ItemCreate) -> dict[str, Any]:
    items = load_items()

    next_id = max((existing["id"] for existing in items), default=0) + 1

    new_item = {
        "id": next_id,
        "name": item.name,
        "status": item.status,
    }

    items.append(new_item)
    save_items(items)

    logger.info(
        "item_created",
        extra={
            "request_id": "application",
        },
    )

    return new_item