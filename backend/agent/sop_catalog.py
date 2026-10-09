"""
Standard Operating Procedures (SOP) Catalog for HeatOps

This is the authoritative list of interventions that municipal departments
are ACTUALLY CAPABLE of executing during a heat emergency.

The AI agent selects from this catalog based on:
- Severity level (CRITICAL / HIGH / MODERATE / LOW)
- Detected resource gaps
- Vulnerable population counts

The agent does NOT invent actions freely — it picks from pre-approved SOPs.
This mirrors how real municipal heat action plans work (e.g., Delhi Heat Action Plan 2024).
"""

from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# SOP Catalog
# Each SOP entry defines:
#   - sop_id       : unique identifier for this intervention
#   - action       : human-readable task description (sent to department)
#   - team         : responsible department
#   - priority     : default priority level
#   - deadline_min : target completion time in minutes
#   - severity     : minimum severity level that triggers this SOP
#   - conditions   : optional conditions that must be true to activate
#   - description  : why this action exists / what it achieves
# ─────────────────────────────────────────────────────────────────────────────

SOP_CATALOG: List[Dict[str, Any]] = [

    # ── WATER DEPARTMENT ─────────────────────────────────────────────────────

    {
        "sop_id": "WD-01",
        "action": "Dispatch emergency water tanker to high-stress water point",
        "team": "Water Dept",
        "priority": "CRITICAL",
        "deadline_min": 15,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["water_gap"],
        "description": (
            "Deploy mobile water tanker to identified water-scarce zones. "
            "Mandated under Delhi Heat Action Plan SOP 3.1 for heat index > 45°C."
        ),
    },
    {
        "sop_id": "WD-02",
        "action": "Open additional drinking water kiosks at high-footfall public areas",
        "team": "Water Dept",
        "priority": "HIGH",
        "deadline_min": 30,
        "trigger_severity": ["HIGH"],
        "conditions": ["water_gap"],  # Only if resource audit finds water gap
        "description": (
            "Activate standby water kiosks at bus stops, markets, and construction sites. "
            "Standard SOP under NDMA Heat Wave Management Guidelines 2023."
        ),
    },
    {
        "sop_id": "WD-03",
        "action": "Refill all public drinking water points and verify chlorine residual levels",
        "team": "Water Dept",
        "priority": "HIGH",
        "deadline_min": 45,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["always"],
        "description": (
            "Water department confirms that existing ward water points are functional, refilled, "
            "and safe for public use before peak demand hours."
        ),
    },
    {
        "sop_id": "WD-04",
        "action": "Arrange backup tanker rotation for schools, markets, and transit stops",
        "team": "Water Dept",
        "priority": "HIGH",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["water_gap", "high_vulnerability"],
        "description": (
            "Adds a scheduled tanker rotation when water shortage overlaps with high vulnerability, "
            "prioritising public places where heat exposure is concentrated."
        ),
    },
    {
        "sop_id": "WD-05",
        "action": "Inspect pumps and standposts for heat-related service failure",
        "team": "Water Dept",
        "priority": "MODERATE",
        "deadline_min": 120,
        "trigger_severity": ["MODERATE", "LOW"],
        "conditions": ["always"],
        "description": (
            "Preventive inspection of public water infrastructure so failures are caught "
            "before the ward reaches high or critical severity."
        ),
    },

    # ── LABOUR DEPARTMENT ────────────────────────────────────────────────────

    {
        "sop_id": "LD-01",
        "action": "Enforce mandatory rest breaks for outdoor workers (no outdoor work 12 PM–4 PM)",
        "team": "Labour Dept",
        "priority": "CRITICAL",
        "deadline_min": 20,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["outdoor_workers_present"],
        "description": (
            "Issue legal enforcement notice under Factories Act / Building Workers Act "
            "banning outdoor heavy work during peak heat hours. "
            "Targets {outdoor_workers} registered outdoor workers in this ward."
        ),
    },
    {
        "sop_id": "LD-02",
        "action": "Issue advisory & SMS alert to outdoor workers: mandatory hydration & shade breaks",
        "team": "Labour Dept",
        "priority": "HIGH",
        "deadline_min": 30,
        "trigger_severity": ["HIGH"],
        "conditions": ["outdoor_workers_present"],
        "description": (
            "Bulk SMS and WhatsApp advisory to registered construction & informal sector workers. "
            "Advisory (not enforcement) — appropriate for HIGH severity per SOP LD-02."
        ),
    },
    {
        "sop_id": "LD-03",
        "action": "Notify contractors to shift outdoor work to early morning or evening hours",
        "team": "Labour Dept",
        "priority": "HIGH",
        "deadline_min": 45,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["outdoor_workers_present"],
        "description": (
            "Labour department contacts registered contractors and site supervisors to move "
            "non-essential outdoor labour away from peak heat exposure windows."
        ),
    },
    {
        "sop_id": "LD-04",
        "action": "Deploy field inspectors to construction sites for heat-safety compliance checks",
        "team": "Labour Dept",
        "priority": "CRITICAL",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["outdoor_workers_gt_500"],
        "description": (
            "Field enforcement is used only when critical heat overlaps with a large outdoor "
            "worker population, so inspection capacity is reserved for highest-risk wards."
        ),
    },
    {
        "sop_id": "LD-05",
        "action": "Send precautionary heat-safety bulletin to registered work sites",
        "team": "Labour Dept",
        "priority": "MODERATE",
        "deadline_min": 90,
        "trigger_severity": ["MODERATE"],
        "conditions": ["outdoor_workers_present"],
        "description": (
            "Moderate-severity bulletin reminds employers to maintain water, shade, and rest "
            "arrangements without invoking formal stop-work enforcement."
        ),
    },

    # ── WARD OFFICERS ────────────────────────────────────────────────────────

    {
        "sop_id": "WO-01",
        "action": "Activate Cooling Centre B & open it as 24-hour heat refuge",
        "team": "Ward Officers",
        "priority": "CRITICAL",
        "deadline_min": 30,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["always"],
        "description": (
            "Cooling Centre B (capacity: 500 persons) is a pre-registered municipal facility. "
            "Staff and supplies are pre-positioned. Activation follows SOP WO-01 checklist."
        ),
    },
    {
        "sop_id": "WO-02",
        "action": "Open Cooling Centre B as voluntary daytime refuge (9 AM – 7 PM)",
        "team": "Ward Officers",
        "priority": "HIGH",
        "deadline_min": 45,
        "trigger_severity": ["HIGH"],
        "conditions": ["always"],
        "description": (
            "Voluntary access during HIGH severity — centre open but not mandatory. "
            "Appropriate scaled-down response vs CRITICAL 24-hour activation."
        ),
    },
    {
        "sop_id": "WO-03",
        "action": "Deploy welfare officers for door-to-door check on elderly residents",
        "team": "Ward Officers",
        "priority": "HIGH",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["high_elderly_population"],  # Only if elderly > 1000
        "description": (
            "Ward-level welfare officers visit single-occupancy elderly households. "
            "Targeting {elderly} registered elderly residents in this ward. "
            "Mandated under State Elderly Care Heat Protocol 2022."
        ),
    },
    {
        "sop_id": "WO-04",
        "action": "Broadcast public heat advisory via PA system & ward notice boards",
        "team": "Ward Officers",
        "priority": "MODERATE",
        "deadline_min": 60,
        "trigger_severity": ["MODERATE", "HIGH", "CRITICAL"],
        "conditions": ["always"],
        "description": (
            "Use existing public address infrastructure to issue heat safety messages. "
            "No additional resources required — uses in-place ward PA system."
        ),
    },
    {
        "sop_id": "WO-05",
        "action": "Activate ward-level heat monitoring: report temperature readings every 2 hours",
        "team": "Ward Officers",
        "priority": "LOW",
        "deadline_min": 120,
        "trigger_severity": ["LOW", "MODERATE"],
        "conditions": ["always"],
        "description": (
            "Ward officer records and submits weather readings via mobile app to command centre. "
            "Standard monitoring SOP — no physical resources deployed."
        ),
    },
    {
        "sop_id": "WO-06",
        "action": "Open temporary shade tents near markets and bus stops",
        "team": "Ward Officers",
        "priority": "HIGH",
        "deadline_min": 75,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["cooling_gap"],
        "description": (
            "Ward officers deploy temporary shade where permanent cooling centre capacity is "
            "insufficient for the exposed population."
        ),
    },
    {
        "sop_id": "WO-07",
        "action": "Coordinate community volunteers for queue management at cooling centres",
        "team": "Ward Officers",
        "priority": "MODERATE",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["cooling_gap"],
        "description": (
            "Volunteer coordination keeps cooling-centre access orderly when demand is expected "
            "to exceed available capacity."
        ),
    },
    {
        "sop_id": "WO-08",
        "action": "Check Anganwadi centres and schools for child heat-safety readiness",
        "team": "Ward Officers",
        "priority": "HIGH",
        "deadline_min": 90,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["high_child_population"],
        "description": (
            "Ward officers verify shaded rooms, drinking water, and guardian communication at "
            "child-facing facilities when child exposure is significant."
        ),
    },

    # ── HEALTH DEPARTMENT ────────────────────────────────────────────────────

    {
        "sop_id": "HD-01",
        "action": "Alert Primary Health Centre: activate heatstroke triage & pre-stock ORS packets",
        "team": "Health Dept",
        "priority": "CRITICAL",
        "deadline_min": 45,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["always"],
        "description": (
            "PHC is instructed to clear emergency beds, stock ORS, and brief staff on heatstroke protocol. "
            "Follows Ministry of Health Heat-Related Illness Management Guidelines 2023."
        ),
    },
    {
        "sop_id": "HD-02",
        "action": "Deploy mobile medical van to high-density outdoor worker zones",
        "team": "Health Dept",
        "priority": "CRITICAL",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["outdoor_workers_gt_500"],  # Only if > 500 outdoor workers
        "description": (
            "Mobile PHC van stationed near construction sites and markets with ORS, "
            "first aid, and heatstroke response kit. Triggered when outdoor worker count > 500."
        ),
    },
    {
        "sop_id": "HD-03",
        "action": "Issue public health advisory: heat safety guidelines & ORS distribution points",
        "team": "Health Dept",
        "priority": "MODERATE",
        "deadline_min": 60,
        "trigger_severity": ["HIGH", "MODERATE"],
        "conditions": ["always"],
        "description": (
            "Distribute heat safety leaflets and announce ORS availability at primary health centres. "
            "Standard public communication SOP — no emergency resources required."
        ),
    },
    {
        "sop_id": "HD-04",
        "action": "Pre-position ambulance at Primary Health Centre for heatstroke transfers",
        "team": "Health Dept",
        "priority": "CRITICAL",
        "deadline_min": 45,
        "trigger_severity": ["CRITICAL"],
        "conditions": ["high_vulnerability"],
        "description": (
            "Ambulance standby is reserved for critical wards with high vulnerability, where "
            "heatstroke transfer demand is most likely to exceed routine response."
        ),
    },
    {
        "sop_id": "HD-05",
        "action": "Set up ORS distribution desk at cooling centre and health centre",
        "team": "Health Dept",
        "priority": "HIGH",
        "deadline_min": 60,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["always"],
        "description": (
            "Health department operates ORS access points at municipal facilities; this supports "
            "hydration without assigning logistics work outside health authority."
        ),
    },
    {
        "sop_id": "HD-06",
        "action": "Notify ASHA workers to call elderly and medically vulnerable residents",
        "team": "Health Dept",
        "priority": "HIGH",
        "deadline_min": 90,
        "trigger_severity": ["CRITICAL", "HIGH"],
        "conditions": ["high_elderly_population"],
        "description": (
            "ASHA phone outreach checks symptoms and medication risks for elderly residents, "
            "complementing ward officer door-to-door welfare checks."
        ),
    },
    {
        "sop_id": "HD-07",
        "action": "Review emergency department heat illness register and report cases every 4 hours",
        "team": "Health Dept",
        "priority": "MODERATE",
        "deadline_min": 120,
        "trigger_severity": ["MODERATE", "HIGH", "CRITICAL"],
        "conditions": ["always"],
        "description": (
            "Health facility reporting gives the command centre early warning if heat illness "
            "cases begin rising faster than forecast risk alone suggests."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Selector function: agent calls this to get the right SOPs
# ─────────────────────────────────────────────────────────────────────────────

def select_sops(
    severity: str,
    outdoor_workers: int = 0,
    elderly: int = 0,
    children: int = 0,
    vulnerability_score: float = 0,
    has_water_gap: bool = False,
    has_cooling_gap: bool = False,
) -> List[Dict[str, Any]]:
    """
    Returns the list of SOPs to activate given the detected conditions.
    The AI agent calls this instead of inventing tasks.
    """
    selected = []

    for sop in SOP_CATALOG:
        # 1. Check severity matches
        if severity not in sop["trigger_severity"]:
            continue

        # 2. Check all conditions
        conditions = sop["conditions"]
        passes = True
        for cond in conditions:
            if cond == "always":
                continue
            elif cond == "water_gap" and not has_water_gap:
                passes = False; break
            elif cond == "cooling_gap" and not has_cooling_gap:
                passes = False; break
            elif cond == "outdoor_workers_present" and outdoor_workers == 0:
                passes = False; break
            elif cond == "high_elderly_population" and elderly <= 1000:
                passes = False; break
            elif cond == "high_child_population" and children <= 3000:
                passes = False; break
            elif cond == "outdoor_workers_gt_500" and outdoor_workers <= 500:
                passes = False; break
            elif cond == "high_vulnerability" and vulnerability_score < 8:
                passes = False; break

        if passes:
            selected.append(sop)

    return selected


def format_action(sop: Dict[str, Any], outdoor_workers: int = 0, elderly: int = 0) -> str:
    """Fills in population placeholders in action strings."""
    action = sop["action"]
    if "{outdoor_workers}" in action:
        action = action.replace("{outdoor_workers}", f"{outdoor_workers:,}")
    if "{elderly}" in action:
        action = action.replace("{elderly}", f"{elderly:,}")
    return action
