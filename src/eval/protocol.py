"""Reading rule of the protocol checks (section `protocol` of the config)."""

import numpy as np

CONFIRMED, CONTRADICTED, NOT_SEPARATED = "confirmed", "contradicted", "not separated"


def reading(low, high, direction: int) -> str:
    """Conclusion read from the confidence intervals of several differences.

    `direction` -1: every difference is expected below zero; +1: above zero. The
    conclusion is confirmed if every interval lies on the expected side of zero,
    contradicted if at least one interval lies on the other side, not separated
    otherwise (an interval that contains zero, none on the other side)."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    low, high = np.asarray(low, dtype=float) * direction, np.asarray(high, dtype=float) * direction
    low, high = np.minimum(low, high), np.maximum(low, high)  # now: every difference is expected above zero
    if len(low) == 0:
        raise ValueError("no difference to read")
    if (low > 0).all():
        return CONFIRMED
    if (high < 0).any():
        return CONTRADICTED
    return NOT_SEPARATED
