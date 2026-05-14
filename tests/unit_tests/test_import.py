from unittest.mock import MagicMock, patch

import pytest
import requests
from k8s_agent_sandbox.exceptions import SandboxRequestError

import langchain_kubernetes_agent_sandbox
from langchain_kubernetes_agent_sandbox.sandbox import KubernetesAgentSandbox

from deepagents.backends.sandbox import (
    ExecuteResponse,
)

def _make_sandbox(*, timeout: int = 300) -> tuple[KubernetesAgentSandbox, MagicMock]:
    mock_sdk = MagicMock()
    mock_sdk.sandbox_id = "test-sandbox-id"
    sb = KubernetesAgentSandbox(sandbox=mock_sdk, timeout=timeout)
    return sb, mock_sdk

def test_import_kubernetes_agent_sandbox():
    assert langchain_kubernetes_agent_sandbox is not None
    
def test_execute_returns_stdout():
    sb, mock_sdk = _make_sandbox()
    expected = ExecuteResponse(output="hello world", exit_code=0)
    mock_sdk.commands.run.return_value = expected

    result = sb.execute("echo hello world")

    assert result is expected
    mock_sdk.commands.run.assert_called_once_with("echo hello world",
timeout=300)


def test_execute_uses_constructor_default_timeout():
    sb, mock_sdk = _make_sandbox(timeout=120)
    mock_sdk.commands.run.return_value = ExecuteResponse(output="", exit_code=0)

    sb.execute("ls")

    mock_sdk.commands.run.assert_called_once_with("ls", timeout=120)


def test_execute_explicit_timeout_overrides_default():
    sb, mock_sdk = _make_sandbox(timeout=300)
    mock_sdk.commands.run.return_value = ExecuteResponse(output="", exit_code=0)

    sb.execute("sleep 1", timeout=42)

    mock_sdk.commands.run.assert_called_once_with("sleep 1", timeout=42)


def test_execute_none_timeout_falls_back_to_default():
    sb, mock_sdk = _make_sandbox(timeout=77)
    mock_sdk.commands.run.return_value = ExecuteResponse(output="", exit_code=0)

    sb.execute("ls", timeout=None)

    mock_sdk.commands.run.assert_called_once_with("ls", timeout=77)


def test_execute_translates_timeout_to_exit_code_124():
    sb, mock_sdk = _make_sandbox(timeout=10)
    err = SandboxRequestError("timed out")
    err.__cause__ = requests.exceptions.Timeout("read timeout")
    mock_sdk.commands.run.side_effect = err

    result = sb.execute("sleep 999")

    assert result.exit_code == 124
    assert "timed out" in result.output
    assert "10s" in result.output


def test_execute_propagates_non_timeout_sandbox_errors():
    sb, mock_sdk = _make_sandbox()
    err = SandboxRequestError("server error")
    err.__cause__ = requests.exceptions.HTTPError("500")
    mock_sdk.commands.run.side_effect = err

    with pytest.raises(SandboxRequestError, match="server error"):
        sb.execute("ls")