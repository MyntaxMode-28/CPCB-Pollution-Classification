"""
CTE/CTO consent rules and fee calculator.
Sources: Air/Water Act Uniform Consent Guidelines 2025 (G.S.R. 84(E)/85(E)) +
Jan 2026 amendments (G.S.R. 62(E)/63(E)) — validity rule corrected per amendment.
"""

# --- Fee formula: CF = CI * SF * PIF ---

CAPITAL_SLABS = [
    (1_00_00_000, 0.00100),        # <= 1 Cr
    (10_00_00_000, 0.00080),       # <= 10 Cr
    (50_00_00_000, 0.00060),       # <= 50 Cr
    (250_00_00_000, 0.00040),      # <= 250 Cr
    (500_00_00_000, 0.00030),      # <= 500 Cr
    (1000_00_00_000, 0.00020),     # <= 1000 Cr
    (float("inf"), 0.00010),       # > 1000 Cr
]

PIF_MAP = {"Green": 1.00, "Orange": 1.50, "Red": 2.00}
MIN_ANNUAL_FEE = {"Green": 5000, "Orange": 7500, "Red": 10000}


def calculate_consent_fee(capital_investment: float, category: str):
    """CF = CI * SF * PIF, with slab-based scale factor and per-slab base-carryover."""
    if category not in PIF_MAP:
        return None  # White / Not-in-ambit — general formula doesn't apply this way

    pif = PIF_MAP[category]
    remaining = capital_investment
    prev_slab_ceiling = 0
    annual_fee = 0.0

    for ceiling, sf in CAPITAL_SLABS:
        if capital_investment <= prev_slab_ceiling:
            break
        slab_amount = min(capital_investment, ceiling) - prev_slab_ceiling
        if slab_amount > 0:
            annual_fee += slab_amount * sf * pif
        prev_slab_ceiling = ceiling
        if capital_investment <= ceiling:
            break

    annual_fee = max(annual_fee, MIN_ANNUAL_FEE[category])
    cte_fee = min(annual_fee * 2, annual_fee * 2)  # CTE <= 2x annual fee (upper bound)

    return {
        "capital_investment": capital_investment,
        "category": category,
        "annual_fee": round(annual_fee, 2),
        "cte_fee_max": round(cte_fee, 2),
    }


# --- CTO validity rule (CORRECTED per Jan 2026 amendment — supersedes old fixed-years table) ---

def get_cto_validity_info():
    return {
        "rule": "one_time_fee_5_to_25_years",
        "description": (
            "As of the 23 Jan 2026 amendment, Consent to Operate no longer expires on a "
            "fixed category-based schedule. The State Government/UT Administration sets a "
            "one-time fee for any duration the applicant applies for, between 5 and 25 years. "
            "Once granted, CTO remains valid indefinitely until formally cancelled."
        ),
        "superseded_rule": (
            "OUTDATED (pre-Jan-2026, do not use): Red=5yr, Orange=10yr, Green=15yr, "
            "Blue(EES)=+2yr fixed validity."
        ),
        "source": "G.S.R. 62(E)/63(E), 23 Jan 2026, amending G.S.R. 84(E)/85(E), 2025",
    }


# --- CTE/CTO processing timelines (unchanged by the 2026 amendment) ---

CTE_TIMELINE_DAYS = {"Red": 60, "Orange": 45, "Green": 30}
CTO_FIRST_TIMELINE_DAYS = {"Red": 90, "Orange": 60, "Green": 30}
CTO_RENEWAL_TIMELINE_DAYS = {"Red": 120, "Orange": 60, "Green": 30}


def get_processing_timelines(category: str):
    """Statutory maximum decision timelines — if the State Board doesn't decide within
    these, the case escalates to the State Level Monitoring Committee, which must then
    decide within 30 days. Source: Air/Water Uniform Consent Guidelines 2025, para 8."""
    if category not in CTE_TIMELINE_DAYS:
        return None
    return {
        "consent_to_establish_days": CTE_TIMELINE_DAYS[category],
        "consent_to_operate_first_days": CTO_FIRST_TIMELINE_DAYS[category],
        "consent_to_operate_renewal_expansion_days": CTO_RENEWAL_TIMELINE_DAYS[category],
        "escalation_note": (
            "If not decided within these limits, the case may be referred to the State "
            "Level Monitoring Committee, which must dispose of it within 30 further days."
        ),
    }
