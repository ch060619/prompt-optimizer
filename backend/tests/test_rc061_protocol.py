from __future__ import annotations

import pytest
from packages.protocol.rabbit_code_protocol import (
    AgentRequest,
    Message,
    ProtocolError,
    ProtocolErrorCode,
    StreamEvent,
    StreamEventType,
    TextBlock,
)
from pydantic import ValidationError

# RC ID: RC-061. Verify the versioned cross-surface protocol models.


def test_protocol_models_round_trip_request_event_and_error() -> None:
    request = AgentRequest(
        request_id="req-1",
        session_id="session-1",
        message=Message(role="user", content=[TextBlock(text="测试协议")]),
    )
    event = StreamEvent(
        request_id=request.request_id,
        seq=0,
        type=StreamEventType.STARTED,
        payload={"session_id": request.session_id},
    )
    error = ProtocolError(code=ProtocolErrorCode.UNAUTHORIZED, message="需要登录")

    assert AgentRequest.model_validate_json(request.model_dump_json()) == request
    assert StreamEvent.model_validate_json(event.model_dump_json()) == event
    assert error.protocol_version == "v1"


def test_protocol_rejects_unknown_version_and_invalid_sequence() -> None:
    with pytest.raises(ValidationError):
        AgentRequest(protocol_version="v2", request_id="req", session_id="session", message={})
    with pytest.raises(ValidationError):
        StreamEvent(request_id="req", seq=-1, type=StreamEventType.DELTA, payload={})
