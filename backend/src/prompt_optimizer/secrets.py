from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import platform
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from typing import Protocol


class SecretStoreError(RuntimeError):
    """Base error for secure credential storage failures."""


class SecretStoreUnavailableError(SecretStoreError):
    """Raised when the host does not expose a supported secret backend."""


class SecretStore(Protocol):
    def put(self, reference: str, value: str) -> None:
        ...

    def get(self, reference: str) -> str | None:
        ...

    def delete(self, reference: str) -> None:
        ...


def new_secret_reference() -> str:
    return f"secret://rabbit-code/{uuid.uuid4().hex}"


def _validate_reference(reference: str) -> None:
    if not reference.startswith("secret://rabbit-code/") or len(reference) <= len("secret://rabbit-code/"):
        raise ValueError("凭据引用必须是 Rabbit Code opaque reference。")


@dataclass
class MemorySecretStore:
    """Deterministic store for tests and explicitly ephemeral sessions."""

    name: str = "memory"
    values: dict[str, str] = field(default_factory=dict)

    def put(self, reference: str, value: str) -> None:
        _validate_reference(reference)
        if not value:
            raise ValueError("凭据不能为空。")
        self.values[reference] = value

    def get(self, reference: str) -> str | None:
        _validate_reference(reference)
        return self.values.get(reference)

    def delete(self, reference: str) -> None:
        _validate_reference(reference)
        self.values.pop(reference, None)


@dataclass(frozen=True)
class UnavailableSecretStore:
    name: str = "unavailable"

    def put(self, reference: str, value: str) -> None:
        _validate_reference(reference)
        raise SecretStoreUnavailableError("当前系统没有可用的安全凭据存储。")

    def get(self, reference: str) -> str | None:
        _validate_reference(reference)
        raise SecretStoreUnavailableError("当前系统没有可用的安全凭据存储。")

    def delete(self, reference: str) -> None:
        _validate_reference(reference)
        raise SecretStoreUnavailableError("当前系统没有可用的安全凭据存储。")


class LinuxSecretServiceStore:
    name = "linux-secret-service"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("secret-tool")
        if not self.executable:
            raise SecretStoreUnavailableError("Linux Secret Service 的 secret-tool 不可用。")

    def put(self, reference: str, value: str) -> None:
        _validate_reference(reference)
        self._run(
            [
                "store",
                "--label=Rabbit Code Provider Credential",
                "application",
                "rabbit-code",
                "reference",
                reference,
            ],
            input_text=f"{value}\n",
        )

    def get(self, reference: str) -> str | None:
        _validate_reference(reference)
        result = self._run(
            ["lookup", "application", "rabbit-code", "reference", reference],
            allow_missing=True,
        )
        return result.strip() if result else None

    def delete(self, reference: str) -> None:
        _validate_reference(reference)
        self._run(
            ["clear", "application", "rabbit-code", "reference", reference],
            allow_missing=True,
        )

    def _run(
        self,
        arguments: list[str],
        *,
        input_text: str | None = None,
        allow_missing: bool = False,
    ) -> str | None:
        if not self.executable:
            raise SecretStoreUnavailableError("Linux Secret Service 的 secret-tool 不可用。")
        try:
            result = subprocess.run(
                [self.executable, *arguments],
                input=input_text,
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SecretStoreUnavailableError("Linux Secret Service 操作失败。") from exc
        if result.returncode != 0:
            if allow_missing and result.returncode == 1:
                return None
            raise SecretStoreError("Linux Secret Service 操作失败。")
        return result.stdout


class _WindowsCredential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialManagerStore:
    name = "windows-credential-manager"
    _CRED_TYPE_GENERIC = 1
    _CRED_PERSIST_LOCAL_MACHINE = 2
    _ERROR_NOT_FOUND = 1168

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise SecretStoreUnavailableError("Windows Credential Manager 仅在 Windows 上可用。")
        self._advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._advapi32.CredWriteW.argtypes = [ctypes.POINTER(_WindowsCredential), wintypes.DWORD]
        self._advapi32.CredWriteW.restype = wintypes.BOOL
        self._advapi32.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(_WindowsCredential)),
        ]
        self._advapi32.CredReadW.restype = wintypes.BOOL
        self._advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._advapi32.CredDeleteW.restype = wintypes.BOOL
        self._advapi32.CredFree.argtypes = [ctypes.c_void_p]
        self._advapi32.CredFree.restype = None

    def put(self, reference: str, value: str) -> None:
        _validate_reference(reference)
        if not value:
            raise ValueError("凭据不能为空。")
        encoded = value.encode("utf-16-le")
        blob = ctypes.create_string_buffer(encoded)
        credential = _WindowsCredential()
        credential.Type = self._CRED_TYPE_GENERIC
        credential.TargetName = reference
        credential.CredentialBlobSize = len(encoded)
        credential.CredentialBlob = ctypes.cast(blob, ctypes.c_void_p)
        credential.Persist = self._CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = "rabbit-code"
        if not self._advapi32.CredWriteW(ctypes.byref(credential), 0):
            raise SecretStoreError("Windows Credential Manager 写入失败。")

    def get(self, reference: str) -> str | None:
        _validate_reference(reference)
        credential = ctypes.POINTER(_WindowsCredential)()
        if not self._advapi32.CredReadW(
            reference,
            self._CRED_TYPE_GENERIC,
            0,
            ctypes.byref(credential),
        ):
            error = ctypes.get_last_error()
            if error == self._ERROR_NOT_FOUND:
                return None
            raise SecretStoreError("Windows Credential Manager 读取失败。")
        try:
            raw = ctypes.string_at(
                credential.contents.CredentialBlob,
                credential.contents.CredentialBlobSize,
            )
            return raw.decode("utf-16-le")
        finally:
            self._advapi32.CredFree(credential)

    def delete(self, reference: str) -> None:
        _validate_reference(reference)
        if not self._advapi32.CredDeleteW(reference, self._CRED_TYPE_GENERIC, 0):
            if ctypes.get_last_error() != self._ERROR_NOT_FOUND:
                raise SecretStoreError("Windows Credential Manager 删除失败。")


def create_secret_store() -> SecretStore:
    system = platform.system()
    if system == "Windows":
        try:
            return WindowsCredentialManagerStore()
        except SecretStoreUnavailableError:
            return UnavailableSecretStore()
    if system == "Linux":
        try:
            return LinuxSecretServiceStore()
        except SecretStoreUnavailableError:
            return UnavailableSecretStore()
    return UnavailableSecretStore()
