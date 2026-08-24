from unittest.mock import AsyncMock, MagicMock, patch

from src.apps.websocket_events.emitter import notify_group, notify_user


@patch("src.apps.websocket_events.emitter.get_channel_layer")
def test_notify_user_sends_to_correct_group(mock_get_channel_layer):
    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()
    mock_get_channel_layer.return_value = mock_layer

    result = notify_user(user_id=42, event="notification:new", payload={"objet": "x"})

    assert result is True
    mock_layer.group_send.assert_called_once()
    group_name, message = mock_layer.group_send.call_args.args
    assert group_name == "user:42"
    assert message["type"] == "notification.push"
    assert message["event"] == "notification:new"
    assert message["payload"] == {"objet": "x"}


@patch("src.apps.websocket_events.emitter.get_channel_layer")
def test_notify_user_returns_false_when_no_channel_layer_configured(mock_get_channel_layer):
    mock_get_channel_layer.return_value = None
    assert notify_user(user_id=42, event="x", payload={}) is False


@patch("src.apps.websocket_events.emitter.get_channel_layer")
def test_notify_user_never_raises_on_backend_error(mock_get_channel_layer):
    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock(side_effect=RuntimeError("redis down"))
    mock_get_channel_layer.return_value = mock_layer

    # ne doit jamais lever : un échec temps réel ne doit pas casser le flux métier
    assert notify_user(user_id=42, event="x", payload={}) is False


@patch("src.apps.websocket_events.emitter.get_channel_layer")
def test_notify_group_uses_given_group_name(mock_get_channel_layer):
    mock_layer = MagicMock()
    mock_layer.group_send = AsyncMock()
    mock_get_channel_layer.return_value = mock_layer

    result = notify_group("master:7", event="master:update", payload={})

    assert result is True
    group_name, message = mock_layer.group_send.call_args.args
    assert group_name == "master:7"
    assert message["event"] == "master:update"
