# langchain-kubernetes-agent-sandbox

Run agent-generated code inside Kubernetes pods via
[`k8s-agent-sandbox`](https://pypi.org/project/k8s-agent-sandbox/).

`KubernetesAgentSandbox` adapts a `k8s_agent_sandbox.Sandbox` to the
`deepagents.backends.sandbox.BaseSandbox` protocol, so it can be used in two
ways:

1. **As a [`deepagents`](https://github.com/langchain-ai/deepagents) backend** —
   the pod *is* the agent's filesystem and shell; state persists across turns.
2. **As a LangChain tool** — the agent keeps an in-memory virtual filesystem
   and calls an `execute_python` tool that spawns an ephemeral pod per run.

| | Sandbox as backend | Sandbox as tool |
|---|---|---|
| Lifetime | Lives for the whole agent session | Spawned per run, terminated at end |
| State across turns | Yes (files + shell) | No |
| Best for | Long, stateful coding sessions | Stateless code execution, lower idle cost |
| Wiring | One kwarg on `create_deep_agent` | Custom `@tool` + VFS seeding |

## Installation

```bash
pip install langchain-kubernetes-agent-sandbox
```

Requires Python 3.12+. You also need access to a Kubernetes cluster that the
`k8s-agent-sandbox` client can reach (your local kubeconfig context is used by
default).

## Pattern 1: Sandbox as a deepagents backend

The sandbox is created once and passed to `create_deep_agent` as `backend=`.
The agent's shell and file tools are routed to the pod for the lifetime of the
agent.

```python
from deepagents import create_deep_agent
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import SandboxLocalTunnelConnectionConfig

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


sandbox = build_sandbox()

agent = create_deep_agent(
    model="claude-sonnet-4-6",
    backend=sandbox,
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Write a Python script that prints the first 10 primes and run it."},
    ],
})

# When you're done with the session:
sandbox.sandbox.terminate()
```

Files uploaded with `sandbox.upload_files([...])` (absolute paths only) are
visible to the agent for the rest of the session.

## Pattern 2: Sandbox as a tool (`execute_python`)

The agent runs with an in-memory virtual filesystem (`state["files"]`). When it
calls `execute_python`, the tool lazily spawns a sandbox, copies the VFS into
`/app/`, runs the code, and the caller terminates the sandbox at the end of the
run.

```python
import base64
from typing import Annotated

from deepagents import create_deep_agent
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import SandboxLocalTunnelConnectionConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from langchain_kubernetes_agent_sandbox import KubernetesAgentSandbox

SANDBOX_TEMPLATE = "python-3.12"
SANDBOX_NAMESPACE = "agent-sandboxes"
UPLOAD_DIR = "/app"

TOOL_MODE_PROMPT_SUFFIX = (
    "\n\nYou have an `execute_python(code)` tool that runs Python 3 in a fresh "
    "Kubernetes sandbox. The sandbox is spawned on the first call within this "
    "turn and terminated when the turn ends — do not rely on state across "
    "tool calls. Any files in your virtual filesystem are copied into `/app/` "
    "inside the sandbox before each call, so reference uploaded files by their "
    "`/app/<name>` path."
)


def _new_sandbox() -> KubernetesAgentSandbox:
    client = SandboxClient(connection_config=SandboxLocalTunnelConnectionConfig())
    raw = client.create_sandbox(template=SANDBOX_TEMPLATE, namespace=SANDBOX_NAMESPACE)
    return KubernetesAgentSandbox(sandbox=raw)


# Per-run sandbox handle. Replace this module-level dict with whatever
# request-scoped storage your app uses (e.g. Streamlit session_state, a FastAPI
# request, an asyncio context var).
_run: dict = {}


def _get_or_spawn_run_sandbox(vfs_files: dict) -> KubernetesAgentSandbox:
    sb = _run.get("sandbox")
    if sb is not None and sb.sandbox.is_active:
        return sb

    sb = _new_sandbox()
    _run["sandbox"] = sb

    payload: list[tuple[str, bytes]] = []
    for path, data in (vfs_files or {}).items():
        content = data.get("content", "")
        encoding = data.get("encoding", "utf-8")
        raw = base64.b64decode(content) if encoding == "base64" else content.encode("utf-8")
        sb_path = path if path.startswith("/") else f"{UPLOAD_DIR}/{path}"
        payload.append((sb_path, raw))
    if payload:
        sb.upload_files(payload)
    return sb


def _terminate_run_sandbox() -> None:
    sb = _run.pop("sandbox", None)
    if sb is not None:
        try:
            sb.sandbox.terminate()
        except Exception:
            pass


@tool
def execute_python(code: str, state: Annotated[dict, InjectedState]) -> str:
    """Execute a Python 3 snippet in an ephemeral Kubernetes sandbox.

    Files in the agent's virtual filesystem are copied into /app/ before
    execution. Returns combined stdout/stderr with the exit code.
    """
    sb = _get_or_spawn_run_sandbox(state.get("files") or {})
    b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
    cmd = (
        "python3 -c "
        "'import base64,sys;"
        f"exec(compile(base64.b64decode(\"{b64}\").decode(),\"<agent>\",\"exec\"))'"
    )
    resp = sb.execute(cmd)
    return f"exit={resp.exit_code}\n{resp.output}"


agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[execute_python],
    system_prompt="You are a helpful assistant." + TOOL_MODE_PROMPT_SUFFIX,
)

try:
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Plot the first 10 primes."}],
        # Seed the VFS with files the agent should see at /app/<name>:
        # "files": {"/app/data.csv": {"content": "...", "encoding": "utf-8"}},
    })
finally:
    _terminate_run_sandbox()
```

Key points:

- The sandbox is created lazily on the first `execute_python` call within a
  run and reused for subsequent calls in the same run.
- VFS files are seeded into `/app/` before each call; the agent should
  reference them by absolute path (`/app/<name>`).
- The caller is responsible for terminating the per-run sandbox in a `finally`
  block — the tool itself does not own the run's lifecycle.

## Configuring the command timeout

Each `execute` call is bounded by a timeout (default `300` seconds). Override
the default per sandbox, or per call:

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
