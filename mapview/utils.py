# coding=utf-8

__all__ = ["clamp"]

def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))
