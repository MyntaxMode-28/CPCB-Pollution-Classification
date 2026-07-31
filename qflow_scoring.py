"""
Q-FLOW engine v2 — scoring built directly from CPCB's official scoring tables
(Table I: Water, Table II: Air, Table III: Waste), as verified against source material.
PIW = W1+W2+W3, PIA = A1+A2+A3, PIH = H1+H2 (hazardous) or PIH = B (bio-medical) —
sums per the tables' own footers, not maximums.
"""

# ============================================================
# TABLE I — WATER POLLUTANT SCORE (PIw = W1 + W2 + W3)
# ============================================================

def score_w1_organic_load(bod: float = 0, cod: float = 0) -> int:
    """Score based on oxygen demand of wastewater (BOD or COD, whichever is higher-scoring)."""
    bod, cod = bod or 0, cod or 0
    if bod >= 5000 or cod >= 10000:
        return 35
    if (1000 <= bod < 5000) or (5000 <= cod < 10000):
        return 30
    if (500 <= bod < 1000) or (1000 <= cod < 5000):
        return 25
    if (100 <= bod < 500) or (250 <= cod < 1000):
        return 20
    if (10 <= bod < 100) or (50 <= cod < 250):
        return 10
    return 0


W2_OPTIONS = [
    ("Toxic/heavy metals, pesticides, aromatic/chlorinated compounds", 30),
    ("Nutrients — nitrogen compounds, oil & grease, pH <5.5 or >9", 25),
    ("Inorganic dissolved solids from process (RO reject, boiler blowdown)", 20),
    ("Cooling tower / recirculation process water only", 15),
    ("None of the above", 0),
]


def score_w3_industrial(wastewater_kld: float) -> int:
    """Industrial trade effluent quantity score."""
    w = wastewater_kld or 0
    if w >= 500:
        return 35
    if 100 <= w < 500:
        return 30
    if 50 <= w < 100:
        return 25
    if 10 <= w < 50:
        return 20
    if w < 10 and w > 0:
        return 15
    return 0


def score_w3_sewage(sewage_kld: float) -> int:
    """Sewage (STP/building/high-volume) quantity score."""
    s = sewage_kld or 0
    if s >= 5000:
        return 35
    if 2000 <= s < 5000:
        return 30
    if 500 <= s < 2000:
        return 25
    if 100 <= s < 500:
        return 20
    if s < 100 and s > 0:
        return 15
    return 0


# ============================================================
# TABLE II — AIR POLLUTANT SCORE (PIa = A1 + A2 + A3)
# ============================================================

A1_OPTIONS = [
    ("Hazardous Air Pollutants (HAPs) and heavy metals (e.g. Benzene, Cd, Hg, PAHs)", 35),
    ("Halogens, acids, pesticide-based pollutants (HF, HCl, H2S, etc.)", 30),
    ("Combustion pollutants — PM, CO2, CO, NOx, SO2", 25),
    ("Volatile Organic Compounds (VOCs) — Toluene, Xylene, etc.", 20),
    ("None of the above", 0),
]

A2_OPTIONS = [
    ("Fugitive PM/acid mist/VOC emissions from process", 30),
    ("Fugitive PM/acid mist/VOC emissions from storage & handling", 25),
    ("Odour nuisance (binding gums, cements, adhesives, enamels)", 20),
    ("None of the above", 0),
]


def score_a3_fuel(fuel_category: str, fuel_tpd: float) -> int:
    """fuel_category: 'coal_liquid' | 'biomass' | 'cleaner_gaseous' | 'electricity'"""
    f = fuel_tpd or 0
    if fuel_category == "coal_liquid":
        if f >= 24:
            return 35
        if 12 <= f < 24:
            return 30
        if 0 < f < 12:
            return 25
    elif fuel_category == "biomass":
        if f >= 48:
            return 25
        if 24 <= f < 48:
            return 20
        if 0 < f < 24:
            return 15
    elif fuel_category == "cleaner_gaseous":
        if f >= 120:
            return 20
        if 60 <= f < 120:
            return 15
        if 0 < f < 60:
            return 10
    return 0  # electricity or no fuel


# ============================================================
# TABLE III — WASTE POLLUTANT SCORE
# (PIh = H1 + H2 for hazardous-waste sectors, PIh = B for biomedical-waste sectors)
# ============================================================

H1_OPTIONS = [
    ("Flammable/ignitable/corrosive/oxidizing/toxic — requires incineration", 30),
    ("Reactive — requires secured landfill after stabilization/treatment", 25),
    ("Requires direct disposal in secured landfill without stabilization", 20),
    ("High-volume, low-effect waste (contaminated bags/drums/containers)", 10),
]


def score_h2_quantity(hazardous_tpa: float) -> int:
    h = hazardous_tpa or 0
    if h >= 5000:
        return 70
    if 1000 <= h < 5000:
        return 50
    if 200 <= h < 1000:
        return 30
    if 10 <= h < 200:
        return 20
    if h < 10 and h > 0:
        return 10
    return 0


def score_biomedical_beds(beds: int) -> int:
    b = beds or 0
    if b >= 1000:
        return 100
    if 500 <= b < 1000:
        return 80
    if 200 <= b < 500:
        return 60
    if 50 <= b < 200:
        return 50
    if 10 <= b < 50:
        return 40
    if 0 < b < 10:
        return 30
    return 25  # non-bedded facility


# ============================================================
# FINAL PI FORMULA (unchanged — Section 7 of Only_Q-flow.md, not in dispute)
# ============================================================

def describe_w1(bod: float = 0, cod: float = 0) -> str:
    bod, cod = bod or 0, cod or 0
    if bod >= 5000 or cod >= 10000:
        return f"BOD {bod}/COD {cod} mg/l matched Table I row W1-1 (\u226525,000 BOD or \u226510,000 COD)"
    if (1000 <= bod < 5000) or (5000 <= cod < 10000):
        return f"BOD {bod}/COD {cod} mg/l matched Table I row W1-2 (1,000\u20135,000 BOD or 5,000\u201310,000 COD)"
    if (500 <= bod < 1000) or (1000 <= cod < 5000):
        return f"BOD {bod}/COD {cod} mg/l matched Table I row W1-3 (500\u20131,000 BOD or 1,000\u20135,000 COD)"
    if (100 <= bod < 500) or (250 <= cod < 1000):
        return f"BOD {bod}/COD {cod} mg/l matched Table I row W1-4 (100\u2013500 BOD or 250\u20131,000 COD)"
    if (10 <= bod < 100) or (50 <= cod < 250):
        return f"BOD {bod}/COD {cod} mg/l matched Table I row W1-5 (10\u2013100 BOD or 50\u2013250 COD)"
    return "No significant organic load (below Table I thresholds)"


def describe_w3(kld: float, kind: str) -> str:
    label = "industrial effluent" if kind == "industrial" else "sewage"
    thresholds = [500, 100, 50, 10] if kind == "industrial" else [5000, 2000, 500, 100]
    w = kld or 0
    if w >= thresholds[0]:
        return f"{w} KLD {label} matched Table I row W3-1 (\u2265{thresholds[0]} KLD)"
    if thresholds[1] <= w < thresholds[0]:
        return f"{w} KLD {label} matched Table I row W3-2 ({thresholds[1]}\u2013{thresholds[0]} KLD)"
    if thresholds[2] <= w < thresholds[1]:
        return f"{w} KLD {label} matched Table I row W3-3 ({thresholds[2]}\u2013{thresholds[1]} KLD)"
    if thresholds[3] <= w < thresholds[2]:
        return f"{w} KLD {label} matched Table I row W3-4 ({thresholds[3]}\u2013{thresholds[2]} KLD)"
    return f"{w} KLD {label} matched Table I row W3-5 (below {thresholds[3]} KLD)"


def describe_a3(fuel_category: str, tpd: float) -> str:
    f = tpd or 0
    names = {"coal_liquid": "Coal/liquid fuel", "biomass": "Biomass fuel", "cleaner_gaseous": "Cleaner/gaseous fuel"}
    if fuel_category not in names:
        return "Electricity or no fuel — Table II A3 not applicable (0 points)"
    return f"{names[fuel_category]}, {f} TPD matched the corresponding Table II A3 band"


def describe_h2(tpa: float) -> str:
    h = tpa or 0
    if h >= 5000:
        return f"{h} TPA matched Table III row H2-1 (\u22655,000 TPA)"
    if 1000 <= h < 5000:
        return f"{h} TPA matched Table III row H2-2 (1,000\u20135,000 TPA)"
    if 200 <= h < 1000:
        return f"{h} TPA matched Table III row H2-3 (200\u20131,000 TPA)"
    if 10 <= h < 200:
        return f"{h} TPA matched Table III row H2-4 (10\u2013200 TPA)"
    if h > 0:
        return f"{h} TPA matched Table III row H2-5 (below 10 TPA)"
    return "No hazardous waste quantity entered"


def describe_beds(beds: int) -> str:
    b = beds or 0
    if b >= 1000:
        return f"{b} beds matched Table III row B-1 (\u22651,000 beds)"
    if 500 <= b < 1000:
        return f"{b} beds matched Table III row B-2 (500\u2013999 beds)"
    if 200 <= b < 500:
        return f"{b} beds matched Table III row B-3 (200\u2013499 beds)"
    if 50 <= b < 200:
        return f"{b} beds matched Table III row B-4 (50\u2013199 beds)"
    if 10 <= b < 50:
        return f"{b} beds matched Table III row B-5 (10\u201349 beds)"
    if b > 0:
        return f"{b} beds matched Table III row B-6 (below 10 beds)"
    return "Non-bedded facility matched Table III row B-7"


def compute_final_pi(piw: int, pia: int, pih: int) -> dict:
    scores = sorted([piw, pia, pih], reverse=True)
    imax, i2, i3 = scores[0], scores[1], scores[2]
    pi = imax + ((100 - imax) * (i2 + i3)) / 200
    pi = round(pi, 1)
    if pi >= 80:
        category = "Red"
    elif pi >= 55:
        category = "Orange"
    elif pi >= 25:
        category = "Green"
    else:
        category = "White"
    return {"PIW": piw, "PIA": pia, "PIH": pih, "PI": pi, "Category": category}
