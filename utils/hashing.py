"""
Hashing utilities for file link generation.
Matches the Go implementation in utils/hashing.go and types/file.go
"""

import hashlib
from config import Config


def pack_file(file_name: str, file_size: int, mime_type: str, file_id: int) -> str:
    """
    Create an MD5 hash from file properties.
    This matches the Go HashableFileStruct.Pack() method.
    """
    hasher = hashlib.md5()
    
    # Hash each field in order (same as Go implementation)
    hasher.update(file_name.encode('utf-8'))
    hasher.update(str(file_size).encode('utf-8'))
    hasher.update(mime_type.encode('utf-8'))
    hasher.update(str(file_id).encode('utf-8'))
    
    return hasher.hexdigest()


def get_short_hash(full_hash: str) -> str:
    """Get truncated hash based on HASH_LENGTH config."""
    return full_hash[:Config.HASH_LENGTH]


def check_hash(input_hash: str, expected_hash: str) -> bool:
    """Validate input hash against expected full hash."""
    return input_hash == get_short_hash(expected_hash)
