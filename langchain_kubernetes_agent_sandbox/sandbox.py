import k8s_agent_sandbox
import requests
from k8s_agent_sandbox.exceptions import SandboxRequestError

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox

COMMAND_TIMEOUT_EXIT_CODE = 124

class KubernetesAgentSandbox(BaseSandbox):
    def __init__(
        self,
        *,
        sandbox: k8s_agent_sandbox.sandbox.Sandbox,
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
        try:
            result = self.sandbox.commands.run(command, timeout=effective_timeout)
        except SandboxRequestError as e:
            if isinstance(e.__cause__, requests.exceptions.Timeout):
                return ExecuteResponse(
                    output=f"Command timed out after {effective_timeout}s",
                    exit_code=COMMAND_TIMEOUT_EXIT_CODE,
                )
            raise
        output = result.stdout if result.stdout else result.stderr
        return ExecuteResponse(output=output, exit_code=result.exit_code)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        responses: list[FileUploadResponse] = []
        for path, content in files:
            if not path.startswith("/"):
                responses.append(FileUploadResponse(path=path, error="invalid_path"))
                continue
            try:
                self.sandbox.files.write(path, content)
                responses.append(FileUploadResponse(path=path))
            except PermissionError:
                responses.append(
                    FileUploadResponse(path=path, error="permission_denied")
                )
            except IsADirectoryError:
                responses.append(FileUploadResponse(path=path, error="is_directory"))
            except FileNotFoundError:
                responses.append(FileUploadResponse(path=path, error="file_not_found"))
        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        responses: list[FileDownloadResponse] = []
        for path in paths:
            if not path.startswith("/"):
                responses.append(FileDownloadResponse(path=path, error="invalid_path"))
                continue
            if not self.sandbox.files.exists(path):
                responses.append(
                    FileDownloadResponse(path=path, error="file_not_found")
                )
                continue
            try:
                content = self.sandbox.files.read(path)
                responses.append(FileDownloadResponse(path=path, content=content))
            except PermissionError:
                responses.append(
                    FileDownloadResponse(path=path, error="permission_denied")
                )
            except IsADirectoryError:
                responses.append(FileDownloadResponse(path=path, error="is_directory"))
            except FileNotFoundError:
                responses.append(
                    FileDownloadResponse(path=path, error="file_not_found")
                )
        return responses
