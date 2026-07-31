"""
Environmental Compensation (EC) calculator.
EC = PI_ec x N x R x S x LF, floor of Rs.5000/day, exponential repeat-violation multiplier.
R (rupee factor) is permitted by CPCB's methodology to range Rs.100-500, with Rs.250
suggested as a default — not a fixed value. Made user-adjustable within that range.
"""

PI_EC_MAP = {"Red": 80, "Orange": 50, "Green": 30}
R_FACTOR_DEFAULT = 250
R_FACTOR_MIN = 100
R_FACTOR_MAX = 500

S_MAP = {"micro_small": 0.5, "medium": 1.0, "large": 1.5}
LF_MAP = {"lt_1m": 1.0, "1_5m": 1.25, "5_10m": 1.5, "gte_10m": 2.0, "gt_10km_boundary": 1.0}
MULTIPLIER_MAP = {"first": 1, "rep1": 2, "rep2": 4, "rep3plus": 8}


def calculate_ec(category, days, scale_key, location_key, repeat_key, r_factor=None):
    if category not in PI_EC_MAP:
        return None  # White / Not-in-ambit: general EC formula not applicable

    if r_factor is None:
        r_factor = R_FACTOR_DEFAULT
    r_factor = max(R_FACTOR_MIN, min(R_FACTOR_MAX, r_factor))  # clamp to permitted range

    pi_ec = PI_EC_MAP[category]
    s = S_MAP.get(scale_key, 1.0)
    lf = LF_MAP.get(location_key, 1.0)
    multiplier = MULTIPLIER_MAP.get(repeat_key, 1)

    ec_base = pi_ec * days * r_factor * s * lf
    floor = 5000 * days
    ec_base = max(ec_base, floor)
    ec_final = ec_base * multiplier

    return {
        "PI_ec": pi_ec,
        "days": days,
        "R": r_factor,
        "S": s,
        "LF": lf,
        "multiplier": multiplier,
        "EC_base": round(ec_base, -2),
        "EC_final": round(ec_final, -2),
    }
