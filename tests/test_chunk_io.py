import io
import struct
import pytest
from k2_blender.core.chunk_io import K2ChunkReader, K2ChunkWriter, ChunkIOError

def test_chunk_writer_and_reader_roundtrip():
    out = io.BytesIO()
    writer = K2ChunkWriter(out, signature=b"SMDL")
    
    payload1 = b"Hello, K2 Engine!"
    writer.write_chunk(b"head", payload1)
    
    payload2 = struct.pack("<4i", 10, 20, 30, 40)
    writer.write_chunk(b"bone", payload2)
    
    raw_data = out.getvalue()
    
    # Verify signature
    assert raw_data[:4] == b"SMDL"
    
    # Read back with K2ChunkReader
    reader = K2ChunkReader(io.BytesIO(raw_data), expected_signature=b"SMDL")
    chunks = list(reader.iter_chunks())
    
    assert len(chunks) == 2
    assert chunks[0].name == b"head"
    assert chunks[0].data == payload1
    assert chunks[1].name == b"bone"
    assert chunks[1].data == payload2

def test_chunk_reader_invalid_signature():
    corrupted = b"XXXX\x00\x00\x00\x00"
    with pytest.raises(ChunkIOError, match="Invalid signature"):
        K2ChunkReader(io.BytesIO(corrupted), expected_signature=b"SMDL")

def test_chunk_reader_truncated_header():
    # Only 2 bytes instead of 8 bytes for chunk header
    stream = io.BytesIO(b"SMDLhe")
    reader = K2ChunkReader(stream, expected_signature=b"SMDL")
    with pytest.raises(ChunkIOError, match="Truncated chunk header"):
        list(reader.iter_chunks())

def test_chunk_reader_truncated_payload():
    stream = io.BytesIO()
    stream.write(b"SMDL")
    stream.write(b"head")
    stream.write(struct.pack("<i", 100)) # claims 100 bytes
    stream.write(b"short payload") # only 13 bytes
    
    reader = K2ChunkReader(io.BytesIO(stream.getvalue()), expected_signature=b"SMDL")
    with pytest.raises(ChunkIOError, match="Truncated chunk payload"):
        list(reader.iter_chunks())

def test_chunk_writer_invalid_chunk_name():
    out = io.BytesIO()
    writer = K2ChunkWriter(out, signature=b"SMDL")
    with pytest.raises(ValueError, match="Chunk name must be 4 bytes"):
        writer.write_chunk(b"toolongname", b"data")
