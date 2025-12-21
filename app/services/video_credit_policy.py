import math


def credits_required(duration_seconds: int) -> int:
    """
    Rule:
    1 credit = 5 seconds of video
    """
    return math.ceil(duration_seconds / 5)
