"""Standard integration tests for KubernetesAgentSandbox.

REQUIREMENTS — these tests will NOT run unless:
  1. A reachable Kubernetes cluster is configured (current kubectl context),
     with the agent-sandbox operator installed and a sandbox template available.
  2. The environment variable K8S_LOCAL_INTEGRATION=1 is set.

The tests hit a real cluster: they create a real pod, exec real commands, and
delete the pod on teardown. They are intended for local dev clusters
(kind / minikube / Docker Desktop). Do not run against production.

Run locally with:
    K8S_LOCAL_INTEGRATION=1 \\
    K8S_SANDBOX_TEMPLATE=<template-name> \\
    uv run python -m pytest tests/integration_tests
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from k8s_agent_sandbox import SandboxClient
from langchain_tests.integration_tests import SandboxIntegrationTests

from langchain_kubernetes_agent_sandbox import KubernetesAgentSandbox

if TYPE_CHECKING:
    from collections.abc import Iterator

    from deepagents.backends.protocol import SandboxBackendProtocol


pytestmark = pytest.mark.skipif(
    os.getenv("K8S_LOCAL_INTEGRATION") != "1",
    reason=(
        "Integration tests require a local Kubernetes cluster with the "
        "agent-sandbox operator. Set K8S_LOCAL_INTEGRATION=1 to enable."
    ),
)


class TestKubernetesAgentSandboxStandard(SandboxIntegrationTests):
    @property
    def has_async(self) -> bool:
        return False

    @pytest.fixture(scope="class")
    def sandbox(self) -> Iterator[SandboxBackendProtocol]:
        template = os.environ.get("K8S_SANDBOX_TEMPLATE", "default")
        namespace = os.environ.get("K8S_SANDBOX_NAMESPACE", "default")

        client = SandboxClient()
        sb = client.create_sandbox(template=template, namespace=namespace)
        backend = KubernetesAgentSandbox(sandbox=sb)
        try:
            yield backend
        finally:
            client.delete_sandbox(sb.sandbox_id, namespace=namespace)
