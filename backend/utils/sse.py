"""SSE 事件构建工具"""

import json
from typing import Any
from utils.timezone import now_iso


def _now() -> str:
    return now_iso()


def sse_event(event_type: str, data: dict[str, Any]) -> str:
    """构建 SSE 事件字符串"""
    if "timestamp" not in data:
        data["timestamp"] = _now()
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def thinking_event(content: str) -> str:
    return sse_event("thinking", {"content": content})


def intent_event(intent: str, confidence: float, reason: str) -> str:
    return sse_event("intent", {"intent": intent, "confidence": confidence, "reason": reason})


def tool_call_event(tool_name: str, tool_input: dict) -> str:
    return sse_event("tool_call", {"tool_name": tool_name, "tool_input": tool_input})


def tool_result_event(tool_name: str, tool_output: str) -> str:
    return sse_event("tool_result", {"tool_name": tool_name, "tool_output": tool_output})


def token_event(content: str, message_id: str) -> str:
    return sse_event("token", {"content": content, "message_id": message_id})


def done_event(message_id: str, full_content: str, conversation_id: str) -> str:
    return sse_event("done", {
        "message_id": message_id,
        "full_content": full_content,
        "conversation_id": conversation_id,
    })


def error_event(code: str, message: str, message_id: str = "") -> str:
    return sse_event("error", {"code": code, "message": message, "message_id": message_id})
