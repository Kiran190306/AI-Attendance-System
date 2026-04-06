from __future__ import annotations

"""Simple density classification based on people count."""


def classify(count: int) -> str:
    if count < 10:
        return "Low"
    if count < 25:
        return "Medium"
    return "High"
