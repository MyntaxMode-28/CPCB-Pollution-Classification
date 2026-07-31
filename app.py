import os
import sys
from flask import Flask, request, jsonify, session, render_template

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from pipeline import Database
from qflow import QUESTIONS, next_question, compute_pi
from penalty import calculate_ec
from consent import calculate_consent_fee, get_cto_validity_info, get_processing_timelines
from ai_layer import suggest_sector, phrase_result

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "Master_Database.xlsx")
db = Database(DB_PATH)

SEVENTEEN_CATEGORY_KEYWORDS = [
    "aluminium refinery", "aluminium smelter", "chlor alkali", "copper smelter",
    "dyes dye intermediates", "fertilizers urea", "integrated iron and steel",
    "sponge iron", "petroleum oil refineries", "pesticide technical", "petrochemicals",
    "pharmaceuticals manufacturing", "sugar", "power plants", "zinc smelter",
    "tanneries", "distillery", "yeast manufacturing", "breweries", "pulp",
]


def is_17_category(sector_name: str) -> bool:
    name = sector_name.lower()
    return any(kw in name for kw in SEVENTEEN_CATEGORY_KEYWORDS)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/search", methods=["POST"])
def search():
    query = request.json.get("query", "")
    results, status = db.search(query)

    ai_suggested = None
    ai_attempted = False
    ai_raw_suggestion = None
    if status == "none":
        ai_attempted = True
        suggestion = suggest_sector(query)
        ai_raw_suggestion = suggestion
        if suggestion:
            new_results, new_status = db.search(suggestion)
            if new_status != "none":
                results, status = new_results, new_status
                ai_suggested = suggestion

    for r in results:
        if "seventeen_category" in r:
            continue  # already tagged by the corrected 17-category dataset
        if r.get("category") in ("Red", "Orange", "Green", "White") and is_17_category(r["sector"]):
            r["inspection_frequency"] = "Quarterly (17-Category Override)"
            r["seventeen_category"] = True
        else:
            freq_map = {"Red": "6 months", "Orange": "12 months", "Green": "24 months", "White": "No routine"}
            r["inspection_frequency"] = freq_map.get(r.get("category"), "N/A")
            r["seventeen_category"] = False

    response = {"status": status, "results": results, "ai_attempted": ai_attempted}
    if ai_suggested:
        response["ai_suggested"] = ai_suggested  # so the UI can show "did you mean...?"
    if ai_attempted and not ai_suggested:
        response["ai_raw_suggestion"] = ai_raw_suggestion  # None if Ollama unreachable/timed out
    return jsonify(response)


@app.route("/api/consent/fee", methods=["POST"])
def consent_fee():
    data = request.json
    result = calculate_consent_fee(
        capital_investment=float(data.get("capital_investment", 0)),
        category=data.get("category"),
    )
    if result is None:
        return jsonify({"applicable": False, "message": "Fee formula not applicable to this category."})
    validity = get_cto_validity_info()
    timelines = get_processing_timelines(data.get("category"))
    return jsonify({"applicable": True, "fee": result, "validity": validity, "timelines": timelines})


@app.route("/api/qflow/start", methods=["POST"])
def qflow_start():
    session["qflow_answers"] = {}
    session["qflow_current"] = None
    session["qflow_history"] = []
    sector_name = request.json.get("sector_name", "")
    session["qflow_sector"] = sector_name
    qid = next_question(None, {})
    session["qflow_current"] = qid
    q = QUESTIONS[qid]
    return jsonify({"question_id": qid, **q})


FUEL_DEFAULT_UNIT = {1: "tpd", 2: "tpd", 3: "kg_day"}  # coal/liquid, biomass -> TPD; gaseous -> kg/day


def build_question_response(qid, answers, can_go_back):
    q = dict(QUESTIONS[qid])
    if qid == "FUEL_QTY":
        q["default_unit"] = FUEL_DEFAULT_UNIT.get(answers.get("FUEL_TYPE"), "tpd")
    return jsonify({"done": False, "question_id": qid, "can_go_back": can_go_back, **q})


@app.route("/api/qflow/answer", methods=["POST"])
def qflow_answer():
    answers = session.get("qflow_answers", {})
    current = session.get("qflow_current")
    current_q = QUESTIONS[current]

    if current_q["type"] == "numeric":
        value = request.json.get("value")
        try:
            answers[current] = float(value)
        except (TypeError, ValueError):
            answers[current] = 0
    elif current_q["type"] == "numeric_unit":
        value = request.json.get("value")
        unit_key = request.json.get("unit", current_q["units"][0]["key"])
        unit_def = next((u for u in current_q["units"] if u["key"] == unit_key), current_q["units"][0])
        try:
            answers[current] = float(value) * unit_def["to_tpd"]
        except (TypeError, ValueError):
            answers[current] = 0
    else:
        choice = request.json.get("choice")
        answers[current] = int(choice)

    session["qflow_answers"] = answers

    qid = next_question(current, answers)
    history = session.get("qflow_history", [])
    history.append(current)
    session["qflow_history"] = history
    session["qflow_current"] = qid

    if qid is None:
        result = compute_pi(answers)
        session["qflow_result"] = result
        return jsonify({"done": True, "result": result})

    q = QUESTIONS[qid]
    return build_question_response(qid, answers, len(history) > 0)


@app.route("/api/qflow/back", methods=["POST"])
def qflow_back():
    history = session.get("qflow_history", [])
    if not history:
        return jsonify({"error": "No previous question."}), 400
    prev_id = history.pop()
    session["qflow_history"] = history
    answers = session.get("qflow_answers", {})
    answers.pop(prev_id, None)
    session["qflow_answers"] = answers
    session["qflow_current"] = prev_id
    q = QUESTIONS[prev_id]
    return build_question_response(prev_id, answers, len(history) > 0)


@app.route("/api/ec/calculate", methods=["POST"])
def ec_calculate():
    data = request.json
    result = calculate_ec(
        category=data.get("category"),
        days=int(data.get("days", 0)),
        scale_key=data.get("scale_key"),
        location_key=data.get("location_key"),
        repeat_key=data.get("repeat_key"),
        r_factor=float(data["r_factor"]) if data.get("r_factor") else None,
    )
    if result is None:
        return jsonify({"applicable": False,
                         "message": "General EC formula does not apply to this category. "
                                    "Consult SPCB/PCC directly for this activity."})
    return jsonify({"applicable": True, **result})


@app.route("/api/ai/status")
def ai_status():
    from ai_layer import _call_ollama
    reply = _call_ollama("Reply with exactly one word: OK", timeout=25.0)
    if reply:
        return jsonify({"connected": True, "reply": reply})
    return jsonify({"connected": False,
                     "hint": "Ollama not reachable. Run 'ollama ps' in a terminal to check, "
                              "or 'ollama run llama3.2' once to wake it up."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
