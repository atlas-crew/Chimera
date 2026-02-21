"""
Helpers for throughput mode payload sizing and response generation.
"""

import os
from typing import Dict


def bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def int_env(name: str):
    value = os.environ.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def throughput_payload_bytes() -> int:
    bytes_value = int_env('DEMO_THROUGHPUT_PAYLOAD_BYTES')
    if bytes_value and bytes_value > 0:
        return bytes_value

    kb_value = int_env('DEMO_THROUGHPUT_PAYLOAD_KB')
    if kb_value and kb_value > 0:
        return kb_value * 1024

    size_label = os.environ.get('DEMO_THROUGHPUT_PAYLOAD_SIZE', 'small').lower()
    sizes = {
        'small': 2 * 1024,
        'medium': 8 * 1024,
        'large': 64 * 1024
    }
    return sizes.get(size_label, 2 * 1024)


def build_throughput_payload(target_bytes: int) -> str:
    header = '{"mode":"throughput","export_id":"THROUGHPUT-EXPORT","status":"ok","data":"'
    footer = '"}'
    filler_len = max(0, target_bytes - len(header) - len(footer))
    filler = 'A' * filler_len
    return header + filler + footer


def build_payload_cache(default_bytes: int) -> Dict[int, str]:
    sizes = {
        2 * 1024: None,
        8 * 1024: None,
        64 * 1024: None,
        default_bytes: None,
    }
    cache = {}
    for size in sizes:
        cache[size] = build_throughput_payload(size)
    return cache
