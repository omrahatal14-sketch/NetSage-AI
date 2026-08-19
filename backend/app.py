"""
NetSage AI - Backend Application Server
Flask REST API server wired to frontend static assets and templates.
"""

import os
import sys
import json
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# Add backend directory to sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from engine.ai_engine import NetSageAIEngine
from engine.rule_checker import DeterministicRuleChecker

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static")
)

# File paths
CASES_JSON_PATH = os.path.join(BACKEND_DIR, "data", "cases.json")
CASES_CSV_PATH = os.path.join(PROJECT_ROOT, "cases.csv")
RAI_LOG_PATH = os.path.join(BACKEND_DIR, "data", "responsible_ai_log.json")
REVIEWS_STORAGE_PATH = os.path.join(BACKEND_DIR, "data", "human_reviews.json")

# Fallback for CSV if in backend/data
if not os.path.exists(CASES_CSV_PATH):
    CASES_CSV_PATH = os.path.join(BACKEND_DIR, "data", "cases.csv")

# Initialize Engines
ai_engine = NetSageAIEngine(cases_path=CASES_JSON_PATH)
rule_checker = DeterministicRuleChecker()

# In-memory store for serverless environments (e.g. Vercel)
IN_MEMORY_USER_REVIEWS = []
TMP_REVIEWS_PATH = "/tmp/human_reviews.json"

def load_cases():
    if os.path.exists(CASES_JSON_PATH):
        with open(CASES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_reviews():
    reviews = []
    seen_ids = set()

    # 1. Base Responsible AI Log
    if os.path.exists(RAI_LOG_PATH):
        try:
            with open(RAI_LOG_PATH, "r", encoding="utf-8") as f:
                for r in json.load(f):
                    reviews.append(r)
                    seen_ids.add(r.get("log_id"))
        except Exception:
            pass

    # 2. In-Memory User Reviews
    for r in IN_MEMORY_USER_REVIEWS:
        if r.get("log_id") not in seen_ids:
            reviews.append(r)
            seen_ids.add(r.get("log_id"))

    # 3. Persistent Local / /tmp File Reviews
    for path in [REVIEWS_STORAGE_PATH, TMP_REVIEWS_PATH]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for r in json.load(f):
                        if r.get("log_id") not in seen_ids:
                            reviews.append(r)
                            seen_ids.add(r.get("log_id"))
            except Exception:
                pass

    return reviews

def save_user_review(new_review):
    global IN_MEMORY_USER_REVIEWS
    IN_MEMORY_USER_REVIEWS.insert(0, new_review)

    # Attempt to persist to disk (local dev or /tmp on Vercel)
    for path in [REVIEWS_STORAGE_PATH, TMP_REVIEWS_PATH]:
        try:
            user_reviews = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    user_reviews = json.load(f)
            user_reviews.insert(0, new_review)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(user_reviews, f, indent=2)
            break
        except Exception:
            continue

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cases", methods=["GET"])
def get_cases():
    cases = load_cases()
    category = request.args.get("category")
    severity = request.args.get("severity")
    osi_layer = request.args.get("osi_layer")

    filtered = cases
    if category:
        filtered = [c for c in filtered if c.get("concept_tag", "").lower() == category.lower()]
    if severity:
        filtered = [c for c in filtered if c.get("severity", "").lower() == severity.lower()]
    if osi_layer:
        filtered = [c for c in filtered if c.get("osi_layer", "").lower() == osi_layer.lower()]

    return jsonify({"count": len(filtered), "cases": filtered})

@app.route("/api/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    cases = load_cases()
    for c in cases:
        if c.get("case_id", "").upper() == case_id.upper():
            return jsonify(c)
    return jsonify({"error": "Case not found"}), 404

@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json() or {}
    case_id = data.get("case_id")
    symptom = data.get("symptom", "")
    topology_notes = data.get("topology_notes", "")
    show_outputs = data.get("show_outputs", "")
    api_key = data.get("api_key")

    result = ai_engine.diagnose_case(
        case_id=case_id,
        symptom=symptom,
        topology_notes=topology_notes,
        show_outputs=show_outputs,
        api_key=api_key
    )
    return jsonify(result)

@app.route("/api/rule_check", methods=["POST"])
def check_rules():
    data = request.get_json() or {}
    show_outputs = data.get("show_outputs", "")
    symptom = data.get("symptom", "")
    topology_notes = data.get("topology_notes", "")

    findings = rule_checker.run_all_checks(
        show_outputs=show_outputs,
        symptom=symptom,
        topology_notes=topology_notes
    )
    return jsonify({
        "count": len(findings),
        "findings": findings
    })

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    reviews = load_reviews()
    return jsonify({"count": len(reviews), "reviews": reviews})

@app.route("/api/reviews", methods=["POST"])
def submit_review():
    data = request.get_json() or {}
    case_id = data.get("case_id", "CUSTOM")
    verdict = data.get("verdict", "Accepted")
    reviewer = data.get("reviewer", "Network Engineer")
    notes = data.get("notes", "")
    corrected_fix = data.get("corrected_fix", "")
    error_category = data.get("error_category", "Human Verified")
    original_ai = data.get("original_ai", {})

    cases = load_cases()
    case_title = "Custom Scenario"
    for c in cases:
        if c["case_id"] == case_id:
            case_title = c["title"]
            break

    review_entry = {
        "log_id": f"REV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "case_id": case_id,
        "case_title": case_title,
        "reviewer": reviewer,
        "review_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "verdict": verdict,
        "error_category": error_category if verdict != "Accepted" else "Validated Correct",
        "original_ai_diagnosis": original_ai,
        "human_correction": {
            "root_cause": notes if verdict != "Accepted" else original_ai.get("root_cause", ""),
            "corrected_fix": corrected_fix if verdict == "Edited" else (original_ai.get("recommended_fix_steps", []) if verdict == "Accepted" else "Fix Rejected"),
            "reviewer_notes": notes
        },
        "lesson_learned": notes if notes else "Human validation confirmed diagnosis safety.",
        "guardrail_implemented": "Review logged in NetSage Responsible AI Audit Trail."
    }

    save_user_review(review_entry)
    return jsonify({"status": "success", "review": review_entry}), 201

@app.route("/api/stats", methods=["GET"])
def get_stats():
    cases = load_cases()
    reviews = load_reviews()

    category_counts = {}
    severity_counts = {}
    osi_counts = {}
    for c in cases:
        cat = c.get("concept_tag", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        sev = c.get("severity", "Medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        osi = c.get("osi_layer", "Layer 3")
        osi_counts[osi] = osi_counts.get(osi, 0) + 1

    verdict_counts = {"Accepted": 0, "Edited": 0, "Rejected": 0}
    for r in reviews:
        v = r.get("verdict", "Accepted")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    total_reviews = sum(verdict_counts.values()) or 1
    ai_accuracy_rate = round(((verdict_counts["Accepted"] + (verdict_counts["Edited"] * 0.5)) / total_reviews) * 100, 1)

    return jsonify({
        "total_cases": len(cases),
        "total_reviews": len(reviews),
        "ai_accuracy_rate": ai_accuracy_rate,
        "category_counts": category_counts,
        "severity_counts": severity_counts,
        "osi_counts": osi_counts,
        "verdict_counts": verdict_counts
    })

@app.route("/api/simulate_fix", methods=["POST"])
def simulate_fix():
    data = request.get_json() or {}
    case_id = data.get("case_id")
    commands = data.get("commands", [])
    if isinstance(commands, str):
        commands = [c.strip() for c in commands.splitlines() if c.strip()]

    cases = load_cases()
    target_case = None
    for c in cases:
        if c["case_id"] == case_id:
            target_case = c
            break

    cli_terminal = [
        "[NetSage Packet Tracer Simulator Connected]",
        "Entering configuration mode...",
    ]
    for cmd in commands:
        cli_terminal.append(f"> {cmd}")
        if "shutdown" in cmd.lower() and "no" not in cmd.lower():
            cli_terminal.append("%LINK-5-CHANGED: Interface administratively down")
        elif "no shutdown" in cmd.lower():
            cli_terminal.append("%LINK-3-UPDOWN: Interface GigabitEthernet changed state to up")
            cli_terminal.append("%LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet, changed state to up")
        elif "encapsulation dot1q" in cmd.lower():
            cli_terminal.append("% Subinterface 802.1Q tag re-applied successfully")
        elif "ip nat inside source" in cmd.lower():
            cli_terminal.append("% Dynamic PAT Translation rule updated")
        elif "clear ip dhcp binding" in cmd.lower() or "clear ip nat" in cmd.lower():
            cli_terminal.append("% Table bindings cleared successfully")
        elif "write memory" in cmd.lower() or "copy run start" in cmd.lower():
            cli_terminal.append("[OK] Configuration saved to NVRAM")

    cli_terminal.append("Exiting configuration mode. Applying verification suite...")

    verif_cmd = target_case.get("verification_command", "ping 192.168.1.1") if target_case else "ping target_ip"
    cli_terminal.append(f"> {verif_cmd}")
    cli_terminal.append("Sending 5, 100-byte ICMP Echos, timeout is 2 seconds:")
    cli_terminal.append("!!!!!")
    cli_terminal.append("Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms")
    cli_terminal.append("VERIFICATION STATUS: PASSED - Network Connectivity Fully Restored!")

    return jsonify({
        "status": "success",
        "output": "\n".join(cli_terminal),
        "verification_result": "PASSED"
    })

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    if os.path.exists(CASES_CSV_PATH):
        return send_file(CASES_CSV_PATH, mimetype="text/csv", as_attachment=True, download_name="cases.csv")
    return jsonify({"error": "cases.csv not found"}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
