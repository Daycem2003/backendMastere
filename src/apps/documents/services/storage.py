from pathlib import Path
from typing import Protocol


class StorageBackend(Protocol):
    def upload(self, content, key: str) -> str: ...
    def delete(self, key: str) -> None: ...
    def signed_url(self, key: str, expires_in: int = 300) -> str: ...


class LocalStorageBackend:
    def __init__(self, root: str):
        self.root = Path(root)

    def upload(self, content, key: str) -> str:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            for chunk in content.chunks():
                output.write(chunk)
        return key

    def delete(self, key: str) -> None:
        path = self.root / key
        if path.exists():
            path.unlink()

    def signed_url(self, key: str, expires_in: int = 300) -> str:
        return f"/media/{key}"
