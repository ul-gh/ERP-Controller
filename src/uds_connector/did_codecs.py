"""Data Identifier Specific Codec Classes for uds_connector.

FIXME: Overridden class uses the struct.pack method extensively.
Consider supplying a pack string to the constructor of the base class
instead of overriding encode/decode methods.

"""
from typing import Literal, Never, override

import udsoncan


class UInt8Codec(udsoncan.DidCodec):
    """Codec for UInt8 response and int output."""

    @override
    def encode(self, did_value: int) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(did_value, length=2, byteorder="big")

    @override
    def decode(self, did_payload: bytes) -> int:
        return int.from_bytes(did_payload)

    @override
    def __len__(self) -> Literal[1]:
        # Dynamically handles remaining payload length
        #raise udsoncan.DidCodec.ReadAllRemainingData
        return 1


class UInt16Codec(udsoncan.DidCodec):
    """Codec for UInt16 response and int output."""

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


class Fixed8Codec(udsoncan.DidCodec):
    """Codec for 16-Bit Fixed-Precision Response with Scale and Offset."""

    @override
    def __init__(self, scale: float, offset: int = 0) -> None:
        super().__init__()
        self.scale: float = scale
        self.offset: int = offset

    @override
    def encode(self, did_value: float) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(
            self.offset + int(did_value / self.scale),
            length=1,
            byteorder="big",
        )

    @override
    def decode(self, did_payload: bytes) -> float:
        return self.scale * (int.from_bytes(did_payload) - self.offset)

    @override
    def __len__(self) -> Literal[1]:
        return 1


class Fixed16Codec(udsoncan.DidCodec):
    """Codec for 16-Bit Fixed-Precision Response with Scale and Offset."""

    @override
    def __init__(self, scale: float, offset: int = 0) -> None:
        super().__init__()
        self.scale: float = scale
        self.offset: int = offset

    @override
    def encode(self, did_value: float) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return int.to_bytes(
            self.offset + int(did_value / self.scale),
            length=2,
            byteorder="big",
        )

    @override
    def decode(self, did_payload: bytes) -> float:
        return self.scale * (int.from_bytes(did_payload) - self.offset)

    @override
    def __len__(self) -> Literal[2]:
        return 2


class RawCodec(udsoncan.DidCodec):
    """Raw bytes of the payload without any conversion."""

    @override
    def encode(self, did_value: bytes) -> bytes:  # pyright: ignore[reportIncompatibleMethodOverride]
        return did_value

    @override
    def decode(self, did_payload: bytes) -> bytes:
        return did_payload

    @override
    def __len__(self) -> Never:
        # Dynamically handles remaining payload length
        raise udsoncan.DidCodec.ReadAllRemainingData
