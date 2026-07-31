"""
17-Category Industries — authoritative PI list from Internal_Logic.md.
CORRECTED: the original gazette-derived table had cement plant sub-rows mislabeled
under "Aluminium Smelter" (co-processing / grinding units are cement terms, not
aluminium). Relabeled here based on cross-referencing CPCB's public 17-category
methodology. Flagged with a `corrected` note for transparency.
"""

SEVENTEEN_CATEGORY = [
    {"name": "Aluminium Refinery", "pi": 96.6},
    {"name": "Aluminium Smelter", "pi": 99.1},
    {"name": "Cement plants - with co-processing with CPP", "pi": 100,
     "corrected": "Originally mislabeled under 'Aluminium Smelter' in source transcription; "
                  "relabeled as Cement (co-processing/CPP are cement industry terms)."},
    {"name": "Cement plants - with co-processing without CPP", "pi": 100, "corrected": "See above."},
    {"name": "Cement plants - without co-processing with CPP", "pi": 100, "corrected": "See above."},
    {"name": "Cement plants - without co-processing without CPP", "pi": 92, "corrected": "See above."},
    {"name": "Cement - stand-alone grinding units with CPP", "pi": 97,
     "corrected": "See above.", "remarks": "≥200 TPD units covered under 17 category"},
    {"name": "Cement - stand-alone grinding units without CPP", "pi": 64,
     "corrected": "See above.", "remarks": "≥200 TPD units covered under 17 category"},
    {"name": "Chlor alkali", "pi": 89.5},
    {"name": "Chlor alkali using washed salt", "pi": 87.5},
    {"name": "Chlor alkali using cleaner/gaseous fuel", "pi": 81.6},
    {"name": "Chlor alkali using cleaner/gaseous fuel and washed salt", "pi": 78.1},
    {"name": "Copper Smelter", "pi": 97.8},
    {"name": "Dyes, Dye Intermediates and Pigments produced by chemical synthesis", "pi": 96.3},
    {"name": "Fertilizers (Urea)", "pi": 92.5},
    {"name": "Fertilizers (Calcium Ammonium Nitrate/Ammonium Nitrate)", "pi": 90.5},
    {"name": "Fertilizers (NPK)", "pi": 90.5},
    {"name": "Fertilizers (Straight Phosphatic Fertilizers)", "pi": 90.5},
    {"name": "Integrated iron and steel plants", "pi": 98.3},
    {"name": "Sponge iron with CPP", "pi": 97},
    {"name": "Sponge iron without CPP", "pi": 96.3},
    {"name": "Petroleum oil refineries", "pi": 98.3},
    {"name": "Pesticide technical (organic chemicals based)", "pi": 94},
    {"name": "Pesticide technical (inorganic chemicals based)", "pi": 91},
    {"name": "Petrochemicals (Naphtha cracker)", "pi": 98.5},
    {"name": "Petrochemicals (Gas cracker)", "pi": 96.8},
    {"name": "Petrochemicals (without cracker)", "pi": 88.1},
    {"name": "Petrochemicals (without cracker, cleaner/gaseous fuel)", "pi": 87.5},
    {"name": "Pharmaceuticals manufacturing", "pi": 98.6},
    {"name": "Pharmaceuticals manufacturing using cleaner/gaseous fuel", "pi": 98},
    {"name": "Sugar (excluding khandsari/jaggery)", "pi": 94.5},
    {"name": "Power plants based on coal", "pi": 98.3},
    {"name": "Power plants based on liquid fuels", "pi": 92.5},
    {"name": "Waste to energy power plants", "pi": 97.6},
    {"name": "Biomass-based power plants", "pi": 88.1},
    {"name": "Nuclear energy-based power plants (>220 MW)", "pi": 81.6},
    {"name": "Nuclear energy-based power plants (up to 220 MW)", "pi": 79.9},
    {"name": "Gas-based power plants", "pi": 61.3},
    {"name": "Zinc smelter", "pi": 97.8},
    {"name": "Tanneries (Raw to finish)", "pi": 93.8},
    {"name": "Tanneries (Raw to wet blue)", "pi": 93.8},
    {"name": "Tanneries (Wet blue to finish)", "pi": 90.6},
    {"name": "Vegetable tanning", "pi": 77.5},
    {"name": "Distillery (Molasses based)", "pi": 97.1},
    {"name": "Distillery (Grain based)", "pi": 93.8},
    {"name": "Distillery (Grain based) with DDGS by-product", "pi": 83.8},
    {"name": "Standalone yeast manufacturing units", "pi": 96.8},
    {"name": "Breweries and malteries (wastewater >=100 KLD)", "pi": 81.3},
    {"name": "Breweries and malteries (wastewater <100 KLD)", "pi": 77.5},
    {"name": "Bleached chemical pulp, papers, paperboards", "pi": 98.1},
    {"name": "Unbleached/TCF bleaching pulp, papers, paperboards", "pi": 92.9},
    {"name": "Bleached TCF grades of chemical pulp, paper, paperboard", "pi": 92.9},
    {"name": "Pulp & Paper (With bleaching)", "pi": 89},
    {"name": "Pulp & Paper (Without bleaching, capacity >=15 TPD)", "pi": 86.3},
    {"name": "Pulp & Paper (Without bleaching, capacity <15 TPD)", "pi": 74},
]

for entry in SEVENTEEN_CATEGORY:
    entry["category"] = "Red"  # all 17-category entries are Red by definition, PI >= 61
