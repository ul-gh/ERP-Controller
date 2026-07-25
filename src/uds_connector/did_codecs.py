"""Data Identifier Specific Codec Classes for uds_connector.

FIXME: Overridden class uses the struct.pack method extensively.
Consider supplying a pack string to the constructor of the base class
instead of overriding encode/decode methods.

"""
from typing import Literal, override

import udsoncan


class UInt16Codec(udsoncan.DidCodec):
    """Codec for UInt16 response."""

    @override
    def encode(self, did_value: int) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(did_value, length=2, byteorder="big")

    @override
    def decode(self, did_payload: bytes) -> int:
        return int.from_bytes(did_payload)

    @override
    def __len__(self) -> Literal[2]:
        # Dynamically handles remaining payload length
        #raise udsoncan.DidCodec.ReadAllRemainingData
        return 2

class Int16Codec(udsoncan.DidCodec):
    """Codec for Signed Int16 response."""

    @override
    def encode(self, did_value: int) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(did_value, length=2, byteorder="big", signed=True)

    @override
    def decode(self, did_payload: bytes) -> int:
        return int.from_bytes(did_payload, signed=True)

    @override
    def __len__(self) -> Literal[2]:
        # Dynamically handles remaining payload length
        #raise udsoncan.DidCodec.ReadAllRemainingData
        return 2

class Fixed16Codec(udsoncan.DidCodec):
    """Codec for 16-Bit Fixed-Precision Response with Scale and Offset."""

    @override
    def __init__(self, scale: float, offset: int = 0) -> None:
        super().__init__()
        self.scale: float = scale
        self.offset: int = offset

    @override
    def encode(self, did_value: float) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(self.offset + int(did_value / self.scale),
            length=2, byteorder="big")

    @override
    def decode(self, did_payload: bytes) -> float:
        return self.scale * (int.from_bytes(did_payload) - self.offset)

    @override
    def __len__(self) -> Literal[2]:
        return 2
