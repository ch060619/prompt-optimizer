from __future__ import annotations

import pytest
from packages.protocol.rabbit_code_protocol import (
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
    StreamCursor,
    StreamEventType,
)
from packages.protocol.rabbit_code_protocol.transport import (
    CursorExpiredError,
    DuplicateToolExecutionError,
    StreamClosedError,
    StreamEventLog,
    ToolExecutionLedger,
    encode_sse,
    encode_sse_heartbeat,
)
from pydantic import ValidationError

# RC ID: RC-063. Verify transport boundaries and reconnect semantics.


def test_reconnect_replays_confirmed_events_and_deduplicates_tool_execution() -> None:
    request_id = "request-1"
    log = StreamEventLog()
    ledger: ToolExecutionLedger[str] = ToolExecutionLedger()
    executions = 0

    started = log.append(request_id, StreamEventType.STARTED, {"session_id": "session-1"})
    tool_call = log.append(
        request_id,
        StreamEventType.TOOL_CALL,
        {"call_id": "call-1", "name": "read_file"},
        event_key="tool-call:call-1",
    )

    def run_tool() -> str:
        nonlocal executions
        executions += 1
        return "file-content"

    assert ledger.execute(request_id, "call-1", run_tool) == "file-content"
    assert log.replay(StreamCursor(request_id=request_id, after_seq=started.seq)) == (tool_call,)

    # A reconnect may replay the tool event; the ledger returns the confirmed result.
    assert ledger.execute(request_id, "call-1", run_tool) == "file-content"
    completed = log.append(
        request_id,
        StreamEventType.COMPLETED,
        {"call_id": "call-1", "result": "file-content"},
        event_key="completed:call-1",
    )

    replayed = log.replay(StreamCursor(request_id=request_id, after_seq=started.seq))
    assert [event.seq for event in replayed] == [tool_call.seq, completed.seq]
    assert executions == 1


def test_event_keys_and_sse_ids_make_retries_idempotent() -> None:
    log = StreamEventLog()
    first = log.append(
        "request-2",
        StreamEventType.PROGRESS,
        {"percent": 50},
        event_key="progress:50",
    )
    retry = log.append(
        "request-2",
        StreamEventType.PROGRESS,
        {"percent": 50},
        event_key="progress:50",
    )

    assert retry == first
    encoded = encode_sse(first)
    assert encoded.startswith(f"id: {first.seq}\nevent: progress\n")
    assert '"percent":50' in encoded
    assert encode_sse_heartbeat() == ": heartbeat\n\n"


def test_cancellation_is_idempotent_and_closes_business_events() -> None:
    log = StreamEventLog()
    cancelled = log.cancel("request-3", reason="user_cancelled")

    assert log.cancel("request-3", reason="ignored_retry") == cancelled
    assert log.is_cancelled("request-3") is True
    with pytest.raises(StreamClosedError):
        log.append("request-3", StreamEventType.DELTA, {"text": "late"})


def test_bounded_cursor_failure_is_explicit() -> None:
    log = StreamEventLog(max_events=1)
    log.append("request-4", StreamEventType.STARTED)
    latest = log.append("request-4", StreamEventType.PROGRESS, {"percent": 1})

    with pytest.raises(CursorExpiredError):
        log.replay(StreamCursor(request_id="request-4", after_seq=-1))
    assert log.latest_cursor("request-4").after_seq == latest.seq


def test_json_rpc_request_response_and_error_round_trip() -> None:
    request = JsonRpcRequest(id="control-1", method="window.focus", params={"window": "main"})
    response = JsonRpcResponse(id=request.id, result={"focused": True})
    error = JsonRpcResponse(
        id=request.id,
        error=JsonRpcError(code=-32601, message="Method not found"),
    )

    assert JsonRpcRequest.model_validate_json(request.model_dump_json()) == request
    assert JsonRpcResponse.model_validate_json(response.model_dump_json()) == response
    assert error.error is not None and error.error.code == -32601
    with pytest.raises(ValidationError):
        JsonRpcResponse(id=request.id)
    ledger: ToolExecutionLedger[str] = ToolExecutionLedger()
    with pytest.raises(DuplicateToolExecutionError):
        ledger.execute(
            "request-5",
            "call-1",
            lambda: ledger.execute("request-5", "call-1", lambda: "unreachable"),
        )
