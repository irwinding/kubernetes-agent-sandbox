import k8s_agent_sandbox

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox

class KubernetesAgentSandbox(BaseSandbox):
    def __init__(
        self, 
        *,
        sandbox: k8s_agent_sandbox.Sandbox,
        timeout: int = 300,
        ):
        self.sandbox = sandbox
        self.default_timeout = timeout
    
    @property
    def id(self) -> str:
        return self.sandbox.sandbox_id
    
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        effective_timeout = timeout if timeout is not None else self.default_timeout
        return self.sandbox.commands.run(command, timeout=effective_timeout)

    def upload_file(self, file_path: str, file_content: bytes) -> FileUploadResponse:
        return self.sandbox.files.write(file_path, file_content)

    def download_file(self, file_path: str) -> FileDownloadResponse:
        return self.sandbox.files.read(file_path)