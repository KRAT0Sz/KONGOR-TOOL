"""
Binary Chunk Reader and Writer for K2 Engine file formats.
Fully replaces the deprecated Python standard library 'chunk' module.
Matches CFileManager::BuildBlockList (c_filemanager.cpp:1644-1682).
"""

import struct
from typing import BinaryIO, Generator, NamedTuple

class ChunkIOError(Exception):
    pass

class Chunk(NamedTuple):
    name: bytes
    length: int
    data: bytes

class K2ChunkReader:
    def __init__(self, stream: BinaryIO, expected_signature: bytes):
        self.stream = stream
        self.expected_signature = expected_signature
        
        sig = self.stream.read(4)
        if len(sig) < 4 or sig != expected_signature:
            raise ChunkIOError(
                f"Invalid signature: expected {expected_signature!r}, got {sig!r}"
            )

    def iter_chunks(self) -> Generator[Chunk, None, None]:
        while True:
            header = self.stream.read(8)
            if not header:
                break
            if len(header) < 8:
                raise ChunkIOError("Truncated chunk header")
            
            name, length = struct.unpack("<4si", header)
            if length < 0:
                raise ChunkIOError(f"Corrupted chunk length {length} for {name!r}")
            
            data = self.stream.read(length)
            if len(data) < length:
                raise ChunkIOError(
                    f"Truncated chunk payload for {name!r}: expected {length} bytes, got {len(data)}"
                )
            
            yield Chunk(name=name, length=length, data=data)

class K2ChunkWriter:
    def __init__(self, stream: BinaryIO, signature: bytes):
        if len(signature) != 4:
            raise ValueError(f"Signature must be exactly 4 bytes, got {len(signature)}")
        self.stream = stream
        self.stream.write(signature)

    def write_chunk(self, name: bytes, data: bytes) -> None:
        if len(name) != 4:
            raise ValueError(f"Chunk name must be 4 bytes, got {len(name)} ({name!r})")
        header = struct.pack("<4si", name, len(data))
        self.stream.write(header)
        self.stream.write(data)
