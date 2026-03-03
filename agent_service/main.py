from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import re
import time
import uuid
import asyncio
from threading import Lock
from shared.registry_loader import load_plugins

app = FastAPI()

# ---------------- PLAN VERSION ----------------
PLAN_VERSION = "1.0.0"

TOOL_REGISTRY = load_plugins()
EXECUTOR_URL = "http://127.0.0.1:8001/execute"

# ---------------- CONFIG ----------------
STEP_TIMEOUT_SECONDS = 5

# ---------------- STORES ----------------
IDEMPOTENCY_STORE = {}
IDEMPOTENCY_LOCK = Lock()

TRACE_STORE = {}
TRACE_LOCK = Lock()


# ---------------- REQUEST MODEL ----------------
class AgentRequest(BaseModel):
    user_input: str
    approval_token: str | None = None
    request_id: str | None = None


# ---------------- EXECUTION CONTEXT ----------------
class ExecutionContext:
    def __init__(self):
        self.current_path = None


# ---------------- EXECUTOR CALL ----------------
async def execute_tool_async(tool_name, parameters, approval_token, user_input, trace_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            EXECUTOR_URL,
            json={
                "tool": tool_name,
                "parameters": parameters,
                "approval_token": approval_token,
                "user_input": user_input
            },
            headers={"X-Trace-Id": trace_id}
        )
        return response.json()


# ---------------- TOOL DETECTION ----------------
def detect_tool(action_text: str, context):
    for tool_name, meta in TOOL_REGISTRY.items():
        for pattern in meta["patterns"]:
            if re.search(pattern, action_text):
                params = meta["extractor"](action_text, context)
                if params:
                    return {
                        "tool": tool_name,
                        "parameters": params,
                        "risk_level": meta["risk_level"]
                    }
    return None


# ---------------- MAIN AGENT ----------------
@app.post("/agent_plan")
async def run_agent_plan(request: AgentRequest):

    # ---------------- STRICT IDEMPOTENCY ----------------
    if request.request_id:
        with IDEMPOTENCY_LOCK:
            if request.request_id in IDEMPOTENCY_STORE:
                return IDEMPOTENCY_STORE[request.request_id]

    trace_id = str(uuid.uuid4())
    total_start_time = time.time()

    goal_original = request.user_input
    goal = goal_original.lower()

    execution_trace = []
    context = ExecutionContext()

    separators = [" and then ", " then ", ",", " and "]
    actions = [goal]

    for sep in separators:
        temp = []
        for part in actions:
            temp.extend(part.split(sep))
        actions = temp

    actions = [a.strip() for a in actions if a.strip()]

    for index, action in enumerate(actions):

        tool_call = detect_tool(action, context)

        if not tool_call:
            execution_trace.append({
                "step": index + 1,
                "error": "No matching tool",
                "action": action
            })
            continue

        tool_name = tool_call["tool"]
        parameters = tool_call["parameters"]
        risk_level = tool_call["risk_level"]

        # ---------------- GOVERNANCE ----------------
        if risk_level == "High":
            execution_trace.append({
                "step": index + 1,
                "tool": tool_name,
                "status": "blocked_high_risk"
            })
            break

        if risk_level == "Medium" and request.approval_token != "APPROVE":
            execution_trace.append({
                "step": index + 1,
                "tool": tool_name,
                "status": "awaiting_approval"
            })
            break

        # ---------------- TIMEOUT CONTROL ----------------
        try:
            result = await asyncio.wait_for(
                execute_tool_async(
                    tool_name,
                    parameters,
                    request.approval_token,
                    goal_original,
                    trace_id
                ),
                timeout=STEP_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            execution_trace.append({
                "step": index + 1,
                "tool": tool_name,
                "status": "timeout",
                "trace_id": trace_id
            })
            break

        execution_status = result.get("execution_status")

        execution_trace.append({
            "step": index + 1,
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
            "trace_id": trace_id
        })

        # ---------------- DETERMINISTIC FAILURE STOP ----------------
        if execution_status != "executed":
            break

        if tool_name == "create_folder":
            context.current_path = parameters["path"]

    final_response = {
        "plan_version": PLAN_VERSION,
        "goal": goal_original,
        "trace_id": trace_id,
        "execution_trace": execution_trace,
        "total_time_sec": round(time.time() - total_start_time, 4)
    }

    # ---------------- STORE IDEMPOTENCY ----------------
    if request.request_id:
        with IDEMPOTENCY_LOCK:
            IDEMPOTENCY_STORE[request.request_id] = final_response

    # ---------------- STORE TRACE FOR REPLAY ----------------
    with TRACE_LOCK:
        TRACE_STORE[trace_id] = final_response

    return final_response


# ---------------- REPLAY ENDPOINT ----------------
@app.get("/agent_replay/{trace_id}")
def replay_trace(trace_id: str):
    with TRACE_LOCK:
        result = TRACE_STORE.get(trace_id)

    if not result:
        return {"error": "Trace not found"}

    return result