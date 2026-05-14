from unittest.mock import MagicMock, patch

import langchain_kubernetes_agent_sandbox
from langchain_kubernetes_agent_sandbox.sandbox import KubernetesAgentSandbox

from deepagents.backends.sandbox import (
    ExecuteResponse,
)

def _make_sandbox() -> tuple[KubernetesAgentSandbox, MagicMock]:
    mock_sdk = MagicMock()
    mock_sdk.sandbox_id = "test-sandbox-id"
    sb = KubernetesAgentSandbox(sandbox=mock_sdk)
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