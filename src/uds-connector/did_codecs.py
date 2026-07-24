from udsoncan 

class UInt16Codec(udsoncan.DidCodec):
    def encode(self, val: int) -> bytes:
        return int.to_bytes(val)

    def decode(self, payload: bytes) -> int:
        return int.from_bytes(payload)

    def __len__(self):
        #raise udsoncan.DidCodec.ReadAllRemainingData  # Dynamically handles remaining payload length
        return 2

class Int16Codec(udsoncan.DidCodec):
    def encode(self, val: int) -> bytes:
        return int.to_bytes(val, signed=True)

    def decode(self, payload: bytes) -> int:
        return int.from_bytes(payload, signed=True)

    def __len__(self):
        #raise udsoncan.DidCodec.ReadAllRemainingData  # Dynamically handles remaining payload length
        return 2

class Fixed16Codec(udsoncan.DidCodec):
    def __init__(self, scale: float, offset: int = 0):
        self.scale = scale
        self.offset = offset

    def encode(self, val) -> bytes:
        return int.to_bytes(self.offset + int(val / self.scale))

    def decode(self, payload) -> float:
        return self.scale * (int.from_bytes(payload) - self.offset)

    def __len__(self):
        return 2