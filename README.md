# langchain-kubernetes-agent-sandbox

A [`deepagents`](https://github.com/langchain-ai/deepagents) sandbox backend that
executes agent-generated code inside Kubernetes pods via
[`k8s-agent-sandbox`](https://pypi.org/project/k8s-agent-sandbox/).

It adapts a `k8s_agent_sandbox.Sandbox` to the `deepagents.backends.sandbox.BaseSandbox`
protocol, so a deep agent can run shell commands and read/write files inside an
ephemeral pod.

## Installation

```bash
pip install langchain-kubernetes-agent-sandbox
```

Requires Python 3.12+. You also need access to a Kubernetes cluster that the
`k8s-agent-sandbox` client can reach (your local kubeconfig context is used by
default).

## Usage with deepagents

Build a `KubernetesAgentSandbox` and pass it to your deep agent as its sandbox
backend:

```python
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.connection import SandboxLocalTunnelConnectionConfig

from langchain_kubernetes_agent_sandbox import KubernetesAgentSandbox

SANDBOX_TEMPLATE = "python-3.12"   # any template available in your cluster
SANDBOX_NAMESPACE = "agent-sandboxes"


def build_sandbox() -> KubernetesAgentSandbox:
    client = SandboxClient(connection_config=SandboxLocalTunnelConnectionConfig())
    raw_sandbox = client.create_sandbox(
        template=SANDBOX_TEMPLATE,
        namespace=SANDBOX_NAMESPACE,
    )
    return KubernetesAgentSandbox(sandbox=raw_sandbox)
```

Then wire the sandbox into a deep agent:

```python
from deepagents import create_deep_agent

sandbox = build_sandbox()

agent = create_deep_agent(
    model="claude-sonnet-4-6",
    sandbox=sandbox,
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Write a Python script that prints the first 10 primes and run it."}],
})
```

The agent's shell and file tools will be routed to the Kubernetes pod through
`KubernetesAgentSandbox`.

### Configuring the command timeout

Each `execute` call is bounded by a timeout (default `300` seconds). Override the
default per sandbox, or per call:

```python
sandbox = KubernetesAgentSandbox(sandbox=raw_sandbox, timeout=120)
sandbox.execute("pytest -q", timeout=600)
```

Commands that exceed the timeout return an `ExecuteResponse` with exit code
`124` instead of raising.

## Capabilities

`KubernetesAgentSandbox` implements the `BaseSandbox` interface:

- `execute(command, *, timeout=None)` — run a shell command in the pod.
- `upload_files([(path, bytes), ...])` — write files into the pod (absolute paths only).
- `download_files([path, ...])` — read files from the pod (absolute paths only).
- `id` — the underlying sandbox ID.

## License

MIT — see [LICENSE](LICENSE).
