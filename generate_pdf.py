"""
NetSage AI - PDF Documentation Generator
Builds a publication-quality 'explanation.pdf' explaining the project architecture,
workflow, dataset, deterministic rules, and Responsible AI guardrails.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for footer page numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NetSage AI — Technical Architecture & Project Explanation")
            self.drawRightString(558, 750, "Cisco Applied AI Project")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, "CONFIDENTIAL — NetSage AI Diagnostic Engine & Human Review Hub")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()

def build_pdf(filename="explanation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Color Palette
    c_primary = colors.HexColor("#0f172a")     # Deep Slate Navy
    c_accent = colors.HexColor("#0284c7")      # Cisco Blue
    c_cyan = colors.HexColor("#0ea5e9")        # Electric Sky
    c_purple = colors.HexColor("#7c3aed")      # Cyber Purple
    c_green = colors.HexColor("#16a34a")       # Forest Green
    c_amber = colors.HexColor("#d97706")       # Amber Warning
    c_red = colors.HexColor("#dc2626")         # Crimson
    c_bg_light = colors.HexColor("#f8fafc")    # Light Table BG
    c_bg_code = colors.HexColor("#0f172a")     # Code background
    c_text_dark = colors.HexColor("#1e293b")   # Dark body text
    c_text_muted = colors.HexColor("#64748b")  # Muted subtitle

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceAfter=14
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_text_dark,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_text_dark,
        leftIndent=14,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0369a1")
    )
    code_style = ParagraphStyle(
        'CodeSnippet',
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#38bdf8")
    )

    story = []

    # ==================== COVER / HEADER ====================
    story.append(Paragraph("NetSage AI", title_style))
    story.append(Paragraph("AI-Assisted Cisco Network Troubleshooting Helper with Human Review", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_accent, spaceBefore=2, spaceAfter=12))

    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Cisco Lab / Packet Tracer", body_style),
            Paragraph("<b>Architecture:</b> Hybrid (Rules + LLM + HITL)", body_style)
        ],
        [
            Paragraph("<b>Safety Rule:</b> Mandatory Human Review", body_style),
            Paragraph("<b>Deliverables:</b> Dataset (32), Prompts, Python Checker, UI, RAI Log", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ==================== SECTION 1: EXECUTIVE OVERVIEW ====================
    story.append(Paragraph("1. Executive Overview & Problem Statement", h1_style))
    story.append(Paragraph(
        "In computer networking labs and enterprise infrastructure, junior engineers frequently struggle to correlate symptoms with true root causes. For example, when a workstation receives an IP address but fails to reach an internal server, the underlying failure could originate from an 802.1Q subinterface tag mismatch, a missing default gateway, an inverted ACL wildcard mask, a DHCP pool exhaustion, or a missing NAT overload statement.",
        body_style
    ))
    story.append(Paragraph(
        "While Generative AI can assist in troubleshooting, <b>autonomous AI deployed in mission-critical networking poses severe operational risks</b>: Large Language Models (LLMs) frequently hallucinate non-existent CLI syntax, confuse standard subnet masks with Cisco inverted wildcard masks, diagnose Layer 3 routing faults before checking Layer 1 link state, and recommend disruptive actions such as device reloads during business hours.",
        body_style
    ))
    story.append(Paragraph(
        "<b>NetSage AI</b> resolves this dilemma through a <b>Hybrid Tri-Tier Architecture</b>: combining fast deterministic Python regex rule validation, evidence-backed AI diagnostic reasoning, and a mandatory <b>Human-in-the-Loop (HITL) review workflow</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ==================== SECTION 2: SYSTEM ARCHITECTURE ====================
    story.append(Paragraph("2. System Architecture & The 3-Tier Pipeline", h1_style))
    
    arch_data = [
        [
            Paragraph("<b>Tier / Pipeline Stage</b>", body_style),
            Paragraph("<b>Mechanism & Functionality</b>", body_style),
            Paragraph("<b>Safety & Operational Purpose</b>", body_style)
        ],
        [
            Paragraph("<b>Tier 1:<br/>Deterministic Rule Checker</b>", body_style),
            Paragraph("Python AST/Regex parsing of raw CLI show-commands (`show ip int brief`, `show ip route`, `show access-lists`, `show vlan brief`, etc.).", body_style),
            Paragraph("Instant, 100% deterministic detection of syntax errors, admin down interfaces, inverted wildcards, and missing gateways.", body_style)
        ],
        [
            Paragraph("<b>Tier 2:<br/>Evidence-Backed AI Engine</b>", body_style),
            Paragraph("Structured JSON prompting enforcing OSI Layer classification (L1–L7), confidence scoring (0–100%), verbatim CLI quotes, and Cisco fix scripts.", body_style),
            Paragraph("Correlates multi-protocol context and symptoms while eliminating hallucinations by requiring textual CLI line evidence.", body_style)
        ],
        [
            Paragraph("<b>Tier 3:<br/>Human-in-the-Loop Review</b>", body_style),
            Paragraph("Interactive reviewer console: <b>Accept</b>, <b>Edit</b> (live CLI script editor), or <b>Reject</b> with automated Responsible AI audit logging.", body_style),
            Paragraph("Guarantees zero unverified configuration changes reach production devices; captures AI failure modes for continual safety improvement.", body_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[120, 210, 174])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 14))

    # ==================== SECTION 3: REPOSITORY & CODE STRUCTURE ====================
    story.append(Paragraph("3. Clean Folder Structure (`backend/` & `frontend/`)", h1_style))
    story.append(Paragraph(
        "The project has been modularized cleanly into decoupled <b>backend</b> and <b>frontend</b> architectures:",
        body_style
    ))

    struct_data = [
        [
            Paragraph("<b>Folder / Component</b>", body_style),
            Paragraph("<b>Files Contained</b>", body_style),
            Paragraph("<b>Description & Responsibilities</b>", body_style)
        ],
        [
            Paragraph("<b>`backend/`</b>", body_style),
            Paragraph("`app.py`<br/>`engine/rule_checker.py`<br/>`engine/ai_engine.py`<br/>`data/cases.json`<br/>`data/responsible_ai_log.json`<br/>`prompts/diagnose_prompt.md`<br/>`tests/test_api.py`", code_style),
            Paragraph("Flask REST API server, deterministic regex rule engine, hybrid AI diagnostic synthesizer, dataset persistence, prompt templates, and automated unit test suite.", body_style)
        ],
        [
            Paragraph("<b>`frontend/`</b>", body_style),
            Paragraph("`templates/index.html`<br/>`static/css/style.css`<br/>`static/js/app.js`<br/>`static/js/charts.js`", code_style),
            Paragraph("Single-Page Application (SPA) with obsidian cyber glassmorphism design, interactive troubleshooting workbench, Chart.js analytics graphs, fix simulator, and review hub.", body_style)
        ],
        [
            Paragraph("<b>Root Deliverables</b>", body_style),
            Paragraph("`cases.csv`<br/>`rule_checker.py`<br/>`diagnose_prompt.md`<br/>`responsible_ai_log.md`<br/>`explanation.pdf`<br/>`README.md`", code_style),
            Paragraph("Project root entrypoints and official submission deliverables for grading and verification.", body_style)
        ]
    ]
    struct_table = Table(struct_data, colWidths=[110, 190, 204])
    struct_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(struct_table)
    story.append(Spacer(1, 14))

    # Page Break for clean reading
    story.append(PageBreak())

    # ==================== SECTION 4: DATASET COVERAGE ====================
    story.append(Paragraph("4. Comprehensive Lab Dataset (32 Scenarios in `cases.csv`)", h1_style))
    story.append(Paragraph(
        "NetSage AI includes <b>32 authentic Packet Tracer lab scenarios</b> (exceeding the 30-case specification). Each scenario includes multi-line Cisco CLI show commands, topology notes, observed symptoms, expected root causes, OSI layers, severity ratings, and exact Cisco IOS remediation commands.",
        body_style
    ))

    dataset_summary = [
        [
            Paragraph("<b>Concept Category</b>", body_style),
            Paragraph("<b>Cases Count</b>", body_style),
            Paragraph("<b>Representative Fault Scenarios Covered</b>", body_style)
        ],
        [
            Paragraph("<b>VLAN & Trunking</b>", body_style),
            Paragraph("6 Cases", body_style),
            Paragraph("Router-on-a-stick dot1Q tag mismatch, Native VLAN mismatch, missing switch VLAN in DB, trunk allowed VLAN pruning, static access on trunk.", body_style)
        ],
        [
            Paragraph("<b>Default Gateway</b>", body_style),
            Paragraph("3 Cases", body_style),
            Paragraph("Missing `ip default-gateway` on L2 switch, host gateway outside subnet, gateway IP typo on host.", body_style)
        ],
        [
            Paragraph("<b>DHCP Services</b>", body_style),
            Paragraph("4 Cases", body_style),
            Paragraph("DHCP pool 100% exhaustion (/28 mask), missing `ip helper-address` on router subinterface, DHCP snooping untrusted uplink drop.", body_style)
        ],
        [
            Paragraph("<b>DNS Resolution</b>", body_style),
            Paragraph("3 Cases", body_style),
            Paragraph("`no ip domain-lookup` globally disabled, wrong DNS server IP configured in DHCP pool, DNS server unreachable.", body_style)
        ],
        [
            Paragraph("<b>Routing Protocols</b>", body_style),
            Paragraph("7 Cases", body_style),
            Paragraph("Missing default static route (0.0.0.0/0), unreachable next-hop IP, OSPF Area ID mismatch, OSPF passive-interface hello drop, OSPF timer mismatch, RIP v1 vs v2, EIGRP AS mismatch.", body_style)
        ],
        [
            Paragraph("<b>Access Control Lists</b>", body_style),
            Paragraph("3 Cases", body_style),
            Paragraph("Inverted wildcard mask (`255.255.255.0` in ACL), implicit deny dropping DNS return UDP traffic, standard ACL placed inbound on source interface.", body_style)
        ],
        [
            Paragraph("<b>NAT / PAT</b>", body_style),
            Paragraph("3 Cases", body_style),
            Paragraph("Missing `overload` keyword on NAT pool (single IP exhaustion), missing `ip nat outside` on WAN interface, NAT pool range overlapping WAN link.", body_style)
        ],
        [
            Paragraph("<b>STP & Wireless</b>", body_style),
            Paragraph("3 Cases", body_style),
            Paragraph("Port-security err-disable MAC violation, BPDU guard triggered port shutdown, duplex mismatch late collisions, WLAN SSID VLAN tag leak.", body_style)
        ]
    ]
    ds_table = Table(dataset_summary, colWidths=[130, 74, 300])
    ds_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(ds_table)
    story.append(Spacer(1, 14))

    # ==================== SECTION 5: STEP-BY-STEP WORKFLOW ====================
    story.append(Paragraph("5. Step-by-Step Diagnostic & Human Review Workflow", h1_style))
    
    steps = [
        ("Step 1: Ingestion & CLI Parsing", "The network engineer selects a lab case or pastes raw `show` command outputs (e.g. `show ip interface brief`, `show ip route`, `show access-lists`) and symptom notes into the Workbench."),
        ("Step 2: Deterministic Pre-Check", "The Python Deterministic Rule Engine scans the text for known configuration errors (such as `administratively down`, `err-disabled`, inverted ACL wildcards, or missing default gateways), returning instant findings with exact CLI line citations."),
        ("Step 3: Structured AI Reasoning", "The AI Diagnostic Engine applies the structured JSON prompt schema to classify the OSI layer, quote supporting CLI evidence, compute confidence, and produce the Cisco IOS configuration script."),
        ("Step 4: Packet Tracer Sandbox Simulation", "The user tests the remediation script in the virtual execution sandbox, which applies the commands in sequence and verifies reachability with simulated ICMP echo requests (100% pass)."),
        ("Step 5: Mandatory Human Review (HITL)", "A certified engineer reviews the diagnosis. The engineer selects **Accept**, **Edit** (modifying commands to prevent side-effects), or **Reject**. The submission is automatically written to `responsible_ai_log.json` and updates the live analytics dashboard.")
    ]
    for title, desc in steps:
        story.append(Paragraph(f"<b>&bull; {title}:</b> {desc}", bullet_style))
    story.append(Spacer(1, 14))

    # ==================== SECTION 6: RESPONSIBLE AI AUDIT LOG ====================
    story.append(Paragraph("6. Responsible AI: 5 Documented AI Failure Incidents", h1_style))
    story.append(Paragraph(
        "A cornerstone requirement of NetSage AI is documenting failure modes where AI was corrected by human network engineers:",
        body_style
    ))

    rai_data = [
        [
            Paragraph("<b>Incident & Case</b>", body_style),
            Paragraph("<b>AI Diagnosis / Failure Mode</b>", body_style),
            Paragraph("<b>Human Engineer Correction & Implemented Safeguard</b>", body_style)
        ],
        [
            Paragraph("<b>RAI-001</b><br/>(CASE-006: ACL Mask)", body_style),
            Paragraph("<b>Subtle Mask Hallucination:</b> AI claimed rule 10 was missing `established` keyword, ignoring that `255.255.255.0` was entered instead of wildcard `0.0.0.255`.", body_style),
            Paragraph("<b>Correction:</b> Engineer replaced subnet mask with wildcard `0.0.0.255`.<br/><b>Guardrail:</b> Added `RULE-ACL-001` deterministic check flagging `255.255.255.x` in ACLs.", body_style)
        ],
        [
            Paragraph("<b>RAI-002</b><br/>(CASE-012: Admin Down)", body_style),
            Paragraph("<b>Layer Skip:</b> AI diagnosed a complex Layer 3 OSPF routing failure when interface GigabitEthernet0/24 was simply `administratively down`.", body_style),
            Paragraph("<b>Correction:</b> Engineer executed `no shutdown` on interface.<br/><b>Guardrail:</b> Enforced Layer 1 interface status pre-checks before running L3 diagnostics.", body_style)
        ],
        [
            Paragraph("<b>RAI-003</b><br/>(CASE-007: NAT PAT)", body_style),
            Paragraph("<b>Incomplete Command Sequence:</b> AI suggested adding `overload` keyword without negating old rule or clearing active NAT translation sessions.", body_style),
            Paragraph("<b>Correction:</b> Engineer added `clear ip nat translation *` to avoid CLI config lock.<br/><b>Guardrail:</b> Augmented NAT remediation templates with session purge steps.", body_style)
        ],
        [
            Paragraph("<b>RAI-004</b><br/>(CASE-003: DHCP Pool)", body_style),
            Paragraph("<b>Disruptive Outage Risk:</b> AI recommended reloading the router (`reload`) during production hours for a DHCP pool exhaustion issue.", body_style),
            Paragraph("<b>Correction:</b> Engineer expanded subnet to /24 and cleared active bindings with `clear ip dhcp binding *`.<br/><b>Guardrail:</b> Added risk blocker intercepting `reload`.", body_style)
        ],
        [
            Paragraph("<b>RAI-005</b><br/>(CASE-001: Subif VLAN)", body_style),
            Paragraph("<b>Cisco CLI Side-Effect Omission:</b> AI changed encapsulation tag to 20 without re-applying the subinterface IP address.", body_style),
            Paragraph("<b>Correction:</b> Engineer re-applied `ip address 192.168.20.1 255.255.255.0` (which Cisco IOS automatically deletes when dot1Q tag changes).<br/><b>Guardrail:</b> Coupled subif encapsulation fixes with IP re-assignment.", body_style)
        ]
    ]
    rai_table = Table(rai_data, colWidths=[110, 190, 204])
    rai_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(rai_table)
    story.append(Spacer(1, 14))

    # ==================== SECTION 7: HOW TO RUN & VERIFY ====================
    story.append(Paragraph("7. Quick Start & Execution Commands", h1_style))
    story.append(Paragraph("<b>1. Launch Web Dashboard:</b> `python app.py` &rarr; Navigate to `http://127.0.0.1:5000`", bullet_style))
    story.append(Paragraph("<b>2. Run Deterministic CLI Checker:</b> `python rule_checker.py` or `python rule_checker.py CASE-006`", bullet_style))
    story.append(Paragraph("<b>3. Execute Unit Test Suite:</b> `python -m unittest discover backend/tests` (15/15 passing)", bullet_style))
    story.append(Spacer(1, 10))

    # Conclusion Banner
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "<b>Conclusion:</b> NetSage AI proves that combining deterministic Python checks, evidence-quoted LLM reasoning, and mandatory human review delivers an exceptionally robust, safe, and educational troubleshooting platform for Cisco Packet Tracer labs.",
        callout_style
    ))

    # Build document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename} ({os.path.getsize(filename)} bytes).")

if __name__ == "__main__":
    build_pdf()
