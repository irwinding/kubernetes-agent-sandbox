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

    def _get_effective_timeout(self, timeout: int | None) -> int:
        return timeout if timeout is not None else self.default_timeout
    
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        effective_timeout = self._get_effective_timeout(timeout)
        return self.sandbox.commands.run(command, timeout=effective_timeout)

    def upload_files(self, files: list[tuple]):
        return super().upload_files(files)
    
    def download_files(self, paths: list[str]):
        download_requests: list = []
        responses: dict[str, FileDownloadResponse] = {}
        
        for path in paths:
            if not path.startswith("/"):
                responses[path] = FileDownloadResponse(path=path, content=None, error="Path must be absolute")
                continue
            download_requests.append(path)
            responses[path] = FileDownloadResponse(path=path, content=None, error=None)
            
        if not download_requests:
            return responses

        for path in download_requests:
            file_exists = self.sandbox.filesystem.exists(path)
            if not file_exists:
                responses[path] = FileDownloadResponse(path=path, content=None, error="File does not exist")
                continue
            try:
                content = self.sandbox.filesystem.read(path)
                responses[path] = FileDownloadResponse(path=path, content=content, error=None)
            except Exception as e:
                responses[path] = FileDownloadResponse(path=path, content=None, error=str(e))
        
        return responses.values()
