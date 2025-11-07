from io import BytesIO

from cryptography.hazmat.primitives import hashes


def hash_bytes(file: BytesIO, chunk_size: int = 4096) -> str:
    """Returns a hex string for a file's crytographically unique hash."""
    digest = hashes.Hash(hashes.SHA256())
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        digest.update(chunk)
    return digest.finalize().hex()
