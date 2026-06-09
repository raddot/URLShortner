import time

class SnowflakeIDGenerator:
    """64-bit unique ID: timestamp(41) + machine_id(10) + sequence(12)."""

    EPOCH = 1700000000000

    def __init__(self, machine_id: int = 1):
        self.machine_id = machine_id & 0x3FF
        self.sequence = 0
        self.last_ts = -1

    def generate(self) -> int:
        ts = int(time.time() * 1000)
        if ts == self.last_ts:
            self.sequence = (self.sequence + 1) & 0xFFF
            if self.sequence == 0:
                while ts <= self.last_ts:
                    ts = int(time.time() * 1000)
        else:
            self.sequence = 0
        self.last_ts = ts
        return ((ts - self.EPOCH) << 22) | (self.machine_id << 12) | self.sequence


BASE62 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def encode_base62(num: int) -> str:
    if num == 0:
        return BASE62[0] * 7
    result = []
    while num:
        result.append(BASE62[num % 62])
        num //= 62
    return "".join(reversed(result)).zfill(7)


id_gen = SnowflakeIDGenerator(machine_id=1)
