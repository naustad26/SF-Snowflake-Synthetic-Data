# Shared utilities for data generators

from faker import Faker
import random

fake = Faker()

_counters: dict[str, int] = {}


def set_seed(seed: int) -> None:
    random.seed(seed)
    Faker.seed(seed)


def next_id(prefix: str) -> str:
    current = _counters.get(prefix, 1)
    _counters[prefix] = current + 1
    return f"{prefix}-{current:06d}"


def generate_phone() -> str:
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"