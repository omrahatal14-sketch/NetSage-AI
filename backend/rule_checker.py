"""
NetSage AI - Deterministic Rule Checker CLI Runner
Run directly with: python rule_checker.py [optional_case_id]
"""

import sys
import json
import os
from engine.rule_checker import DeterministicRuleChecker

def main():
    checker = DeterministicRuleChecker()
    cases_path = os.path.join(os.path.dirname(__file__), "data", "cases.json")

    print("=" * 75)
    print(" NetSage AI - Deterministic Cisco Network Rule Checker Engine")
    print("=" * 75)

    if not os.path.exists(cases_path):
        print(f"Error: {cases_path} not found.")
        return

    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    target_case_id = sys.argv[1].upper() if len(sys.argv) > 1 else None

    if target_case_id:
        target_cases = [c for c in cases if c["case_id"] == target_case_id]
        if not target_cases:
            print(f"Case '{target_case_id}' not found in dataset. Available: {[c['case_id'] for c in cases[:5]]}...")
            return
    else:
        print(f"Loaded {len(cases)} troubleshooting scenarios from dataset.")
        print("Running deterministic checks across sample cases:\n")
        # Run across first 6 distinct concept cases as sample demonstration
        target_cases = cases[:6]

    total_findings = 0
    for c in target_cases:
        print(f"\n" + "-" * 75)
        print(f"Scenario: [{c['case_id']}] {c['title']}")
        print(f"Concept: {c['concept_tag']} | Layer: {c['osi_layer']} | Severity: {c['severity']}")
        print(f"Symptom: {c['symptom']}")
        print("-" * 75)

        findings = checker.run_all_checks(
            show_outputs=c["show_outputs"],
            symptom=c["symptom"],
            topology_notes=c["topology_notes"]
        )

        if not findings:
            print("  [OK] No deterministic rule violations triggered.")
        else:
            for f in findings:
                total_findings += 1
                print(f"\n  [!] RULE TRIGGERED: [{f['rule_id']}] {f['rule_name']}")
                print(f"      OSI Layer:      {f['osi_layer']}")
                print(f"      Category:       {f['category']}")
                print(f"      Severity:       {f['severity']}")
                print(f"      Message:        {f['message']}")
                print(f"      CLI Evidence:   {', '.join(f['evidence'])}")
                print(f"      Suggested Fix:  {f['suggested_fix']}")

    print("\n" + "=" * 75)
    print(f" Verification Complete. Total Deterministic Rule Violations Caught: {total_findings}")
    print("=" * 75)

if __name__ == "__main__":
    main()
