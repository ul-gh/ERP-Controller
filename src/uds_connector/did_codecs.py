"""Data Identifier Specific Codec Classes for uds_connector."""
from typing import Literal, override

import udsoncan


class UInt16Codec(udsoncan.DidCodec):
    """Codec for UInt16 response."""

    @override
    def encode(self, val: int) -> bytes:
        return int.to_bytes(val)

    @override
    def decode(self, payload: bytes) -> int:
        return int.from_bytes(payload)

    @override
    def __len__(self) -> Literal[2]:
        #raise udsoncan.DidCodec.ReadAllRemainingData  # Dynamically handles remaining payload length
        return 2

class Int16Codec(udsoncan.DidCodec):
    """Codec for Signed Int16 response."""

    @override
    def encode(self, val: int) -> bytes:
        return int.to_bytes(val, signed=True)

    @override
    def decode(self, payload: bytes) -> int:
        return int.from_bytes(payload, signed=True)

    @override
    def __len__(self) -> Literal[2]:
        #raise udsoncan.DidCodec.ReadAllRemainingData  # Dynamically handles remaining payload length
        return 2

class Fixed16Codec(udsoncan.DidCodec):
    """Codec for 16-Bit Fixed-Precision Response with Scale and Offset."""

    @override
    def __init__(self, scale: float, offset: int = 0) -> None:
        super().__init__()
        self.scale: float = scale
        self.offset: int = offset

    @override
    def encode(self, val: float) -> bytes:
        return int.to_bytes(self.offset + int(val / self.scale))

    @override
    def decode(self, payload: bytes) -> float:
        return self.scale * (int.from_bytes(payload) - self.offset)

    @override
    def __len__(self) -> Literal[2]:
        return 2
