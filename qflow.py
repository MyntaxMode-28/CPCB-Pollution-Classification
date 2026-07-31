"""
Q-FLOW v2 — question flow controller. Scoring logic lives in qflow_scoring.py
(real CPCB threshold tables). This file only handles: what question comes next,
and collecting answers into a dict that qflow_scoring.py turns into a final PI.
"""
from qflow_scoring import (
    score_w1_organic_load, W2_OPTIONS, score_w3_industrial, score_w3_sewage,
    A1_OPTIONS, A2_OPTIONS, score_a3_fuel,
    H1_OPTIONS, score_h2_quantity, score_biomedical_beds,
    compute_final_pi,
    describe_w1, describe_w3, describe_a3, describe_h2, describe_beds,
)

def _choice_q(text, options):
    """options: list of (label, ) tuples or list of plain strings."""
    labels = [o[0] if isinstance(o, tuple) else o for o in options]
    return {"type": "choice", "text": text, "options": labels}

def _numeric_q(text, unit=""):
    return {"type": "numeric", "text": text, "unit": unit}

def _numeric_unit_q(text, units):
    return {"type": "numeric_unit", "text": text, "units": units}

# Ordered flow. Each step: id -> (question_builder, next_id_resolver)
# next_id_resolver(answers) -> next step id, or None if flow branches elsewhere (handled in next_question)

FLOW = [
    "WATER_TYPE", "BOD_VALUE", "COD_VALUE", "W2_TYPE", "WW_QTY",
    "AIR_PRESENT", "A1_TYPE", "A2_TYPE", "FUEL_TYPE", "FUEL_QTY",
    "WASTE_TYPE", "H1_TYPE", "H2_QTY", "BEDS", "EPR_TYPE",
]

QUESTIONS = {
    "WATER_TYPE": _choice_q(
        "Does this unit generate wastewater?",
        ["No wastewater (dry process)", "Yes — industrial/process effluent", "Yes — sewage only (STP/building)"]),
    "BOD_VALUE": _numeric_q("Approximate BOD (Biochemical Oxygen Demand) of the wastewater", "mg/l — enter 0 if unknown"),
    "COD_VALUE": _numeric_q("Approximate COD (Chemical Oxygen Demand) of the wastewater", "mg/l — enter 0 if unknown"),
    "W2_TYPE": _choice_q("Which best describes other pollutants in the wastewater?", W2_OPTIONS),
    "WW_QTY": _numeric_q("Quantity of wastewater/sewage generated", "KLD (kilolitres per day)"),
    "AIR_PRESENT": _choice_q("Does this unit have air emissions (stack/chimney/process)?", ["No", "Yes"]),
    "A1_TYPE": _choice_q("Which best describes the process emissions?", A1_OPTIONS),
    "A2_TYPE": _choice_q("Which best describes fugitive emissions/odour?", A2_OPTIONS),
    "FUEL_TYPE": _choice_q("Main fuel used?", [
        "Coal or liquid fuels (furnace oil, diesel)", "Biomass-based fuels",
        "Cleaner/gaseous fuels (PNG/CNG/LPG/CBG)", "Electricity or no fuel"]),
    "FUEL_QTY": _numeric_unit_q("Approximate daily fuel consumption", [
        {"key": "tpd", "label": "TPD (tonnes per day)", "to_tpd": 1.0},
        {"key": "kg_day", "label": "kg per day", "to_tpd": 0.001},
    ]),
    "WASTE_TYPE": _choice_q("Type of waste generated?", [
        "Hazardous waste", "Bio-medical waste", "No significant waste"]),
    "H1_TYPE": _choice_q("Which best describes the hazardous waste?", H1_OPTIONS),
    "H2_QTY": _numeric_q("Annual hazardous waste quantity", "TPA (tonnes per annum)"),
    "BEDS": _numeric_q("Number of beds (enter 0 if non-bedded facility)", "beds"),
    "EPR_TYPE": _choice_q("Waste type generated/handled (for EPR Rules applicability)", [
        "Plastic", "Battery", "E-waste", "Used oil", "Tyres", "Multiple", "None"]),
}


def next_question(current_id, answers):
    if current_id is None:
        return "WATER_TYPE"

    idx = FLOW.index(current_id)

    # --- branch logic ---
    if current_id == "WATER_TYPE":
        choice = answers["WATER_TYPE"]
        if choice == 1:  # No wastewater
            return "AIR_PRESENT"
        return "BOD_VALUE"

    if current_id == "COD_VALUE":
        return "W2_TYPE"

    if current_id == "WW_QTY":
        return "AIR_PRESENT"

    if current_id == "AIR_PRESENT":
        if answers["AIR_PRESENT"] == 1:  # No air emissions
            return "WASTE_TYPE"
        return "A1_TYPE"

    if current_id == "A2_TYPE":
        return "FUEL_TYPE"

    if current_id == "FUEL_TYPE":
        fuel_choice = answers["FUEL_TYPE"]
        if fuel_choice == 4:  # Electricity/no fuel
            return "WASTE_TYPE"
        return "FUEL_QTY"

    if current_id == "FUEL_QTY":
        return "WASTE_TYPE"

    if current_id == "WASTE_TYPE":
        w = answers["WASTE_TYPE"]
        if w == 1:  # Hazardous
            return "H1_TYPE"
        if w == 2:  # Bio-medical
            return "BEDS"
        return "EPR_TYPE"  # No significant waste

    if current_id == "H2_QTY":
        return "EPR_TYPE"

    if current_id == "BEDS":
        return "EPR_TYPE"

    if current_id == "EPR_TYPE":
        return None  # done

    # default: linear fallback
    return FLOW[idx + 1] if idx + 1 < len(FLOW) else None


def compute_pi(answers):
    breakdown = []

    # --- Water ---
    water_choice = answers.get("WATER_TYPE")
    if water_choice == 1:
        piw = 0
        breakdown.append("Water: dry process / no wastewater — PIW = 0")
    else:
        w1 = score_w1_organic_load(answers.get("BOD_VALUE", 0), answers.get("COD_VALUE", 0))
        w2_idx = answers.get("W2_TYPE", 5) - 1
        w2 = W2_OPTIONS[w2_idx][1] if 0 <= w2_idx < len(W2_OPTIONS) else 0
        qty = answers.get("WW_QTY", 0)
        kind = "industrial" if water_choice == 2 else "sewage"
        w3 = score_w3_industrial(qty) if water_choice == 2 else score_w3_sewage(qty)
        piw = w1 + w2 + w3  # per Table I footer: PIw = W1 + W2 + W3 (sum, not max)
        breakdown.append(f"Water (W1): {describe_w1(answers.get('BOD_VALUE', 0), answers.get('COD_VALUE', 0))} \u2192 {w1} pts")
        if 0 <= w2_idx < len(W2_OPTIONS):
            breakdown.append(f"Water (W2): \"{W2_OPTIONS[w2_idx][0]}\" \u2192 {w2} pts")
        breakdown.append(f"Water (W3): {describe_w3(qty, kind)} \u2192 {w3} pts")
        breakdown.append(f"PIW = W1 + W2 + W3 = {w1} + {w2} + {w3} = {piw}")

    # --- Air ---
    if answers.get("AIR_PRESENT") == 1:
        pia = 0
        breakdown.append("Air: no emissions reported — PIA = 0")
    else:
        a1_idx = answers.get("A1_TYPE", 5) - 1
        a1 = A1_OPTIONS[a1_idx][1] if 0 <= a1_idx < len(A1_OPTIONS) else 0
        a2_idx = answers.get("A2_TYPE", 4) - 1
        a2 = A2_OPTIONS[a2_idx][1] if 0 <= a2_idx < len(A2_OPTIONS) else 0
        fuel_map = {1: "coal_liquid", 2: "biomass", 3: "cleaner_gaseous", 4: "electricity"}
        fuel_cat = fuel_map.get(answers.get("FUEL_TYPE"), "electricity")
        a3 = score_a3_fuel(fuel_cat, answers.get("FUEL_QTY", 0))
        pia = a1 + a2 + a3  # per Table II footer: PIa = A1 + A2 + A3 (sum, not max)
        if 0 <= a1_idx < len(A1_OPTIONS):
            breakdown.append(f"Air (A1): \"{A1_OPTIONS[a1_idx][0]}\" \u2192 {a1} pts")
        if 0 <= a2_idx < len(A2_OPTIONS):
            breakdown.append(f"Air (A2): \"{A2_OPTIONS[a2_idx][0]}\" \u2192 {a2} pts")
        breakdown.append(f"Air (A3): {describe_a3(fuel_cat, answers.get('FUEL_QTY', 0))} \u2192 {a3} pts")
        breakdown.append(f"PIA = A1 + A2 + A3 = {a1} + {a2} + {a3} = {pia}")

    # --- Waste ---
    waste_choice = answers.get("WASTE_TYPE")
    if waste_choice == 1:  # Hazardous
        h1_idx = answers.get("H1_TYPE", 4) - 1
        h1 = H1_OPTIONS[h1_idx][1] if 0 <= h1_idx < len(H1_OPTIONS) else 0
        h2 = score_h2_quantity(answers.get("H2_QTY", 0))
        pih = h1 + h2
        if 0 <= h1_idx < len(H1_OPTIONS):
            breakdown.append(f"Waste (H1): \"{H1_OPTIONS[h1_idx][0]}\" \u2192 {h1} pts")
        breakdown.append(f"Waste (H2): {describe_h2(answers.get('H2_QTY', 0))} \u2192 {h2} pts")
        breakdown.append(f"PIH = H1 + H2 = {pih}")
    elif waste_choice == 2:  # Bio-medical
        pih = score_biomedical_beds(answers.get("BEDS", 0))
        breakdown.append(f"Waste (B): {describe_beds(answers.get('BEDS', 0))} \u2192 {pih} pts")
    else:
        pih = 0
        breakdown.append("Waste: none significant — PIH = 0")

    result = compute_final_pi(piw, pia, pih)
    result["breakdown"] = breakdown
    return result
