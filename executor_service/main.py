from fastapi import FastAPI, Header
from pydantic import BaseModel
import asyncio
import uuid
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

from shared.registry_loader import load_plugins

app = FastAPI()

# ---------------- REGISTRY ----------------
TOOL_REGISTRY = load_plugins()

# ---------------- THREAD POOL ----------------
EXECUTION_POOL = ThreadPoolExecutor(max_workers=4)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("executor")

def structured_log(data: dict):
    logger.info(json.dumps(data))


# ---------------- METRICS ----------------
EXECUTION_COUNTER = Counter(
    "tool_executions_total",
    "Total number of tool executions",
    ["tool", "status"]
)

EXECUTION_LATENCY = Histogram(
    "tool_execution_duration_seconds",
    "Tool execution latency",
    ["tool"]
)


# ---------------- REQUEST MODEL ----------------
class ExecutionRequest(BaseModel):
    tool: str
    parameters: dict
    approval_token: str | None = None
    user_input: str | None = None


# ---------------- EXECUTION ENDPOINT ----------------
@app.post("/execute")
async def execute_tool(
    request: ExecutionRequest,
    x_trace_id: str | None = Header(default=None)
):

    # If trace_id not provided → generate one (fallback)
    trace_id = x_trace_id or str(uuid.uuid4())

    if request.tool not in TOOL_REGISTRY:
        return {"execution_status": "blocked_unregistered_tool"}

    tool_data = TOOL_REGISTRY[request.tool]
    risk = tool_data["risk_level"]

    if risk == "High":
        return {"execution_status": "blocked_high_risk"}

    if risk == "Medium" and request.approval_token != "APPROVE":
        return {"execution_status": "awaiting_approval"}

    start_time = time.time()

    structured_log({
        "trace_id": trace_id,
        "event": "execution_started",
        "tool": request.tool,
        "parameters": request.parameters
    })

    try:
        loop = asyncio.get_running_loop()

        with EXECUTION_LATENCY.labels(tool=request.tool).time():
            result = await loop.run_in_executor(
                EXECUTION_POOL,
                tool_data["executor"],
                request.parameters
            )

        duration = time.time() - start_time

        EXECUTION_COUNTER.labels(
            tool=request.tool,
            status="success"
        ).inc()

        structured_log({
            "trace_id": trace_id,
            "event": "execution_completed",
            "tool": request.tool,
            "duration_ms": round(duration * 1000, 3),
            "result": result
        })

        return {
            "execution_status": "executed",
            "trace_id": trace_id,
            "execution_result": result
        }

    except Exception as e:

        duration = time.time() - start_time

        EXECUTION_COUNTER.labels(
            tool=request.tool,
            status="failure"
        ).inc()

        structured_log({
            "trace_id": trace_id,
            "event": "execution_failed",
            "tool": request.tool,
            "duration_ms": round(duration * 1000, 3),
            "error": str(e)
        })

        return {
            "execution_status": "error",
            "trace_id": trace_id,
            "execution_result": {
                "detail": str(e)
            }
        }


# ---------------- METRICS ----------------
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")