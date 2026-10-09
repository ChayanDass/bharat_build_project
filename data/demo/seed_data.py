from datetime import datetime, timezone, timedelta
from backend.config import container
from backend.domain.models import (
    Ward, VulnerabilityProfile, Resource, HeatEvent
)
from backend.domain.services import calculate_heat_risk


def seed_demo_data(reset: bool = True):
    # Clear existing tables if reset is True
    if reset and hasattr(container, 'db'):
        with container.db.get_connection() as conn:
            conn.execute("DELETE FROM escalations")
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM action_plans")
            conn.execute("DELETE FROM heat_events")
            conn.execute("DELETE FROM resources")
            conn.execute("DELETE FROM vulnerability_profiles")
            conn.execute("DELETE FROM wards")
            conn.commit()

    ward_repo = container.ward_repo
    vuln_repo = container.vulnerability_repo
    res_repo = container.resource_repo
    event_repo = container.event_repo

    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------
    # WARD 12 (Critical Demo Ward)
    # -------------------------------------------------------------
    w12 = Ward(
        ward_id="ward_12",
        name="Ward 12 — Karol Bagh North",
        city="Delhi",
        population=45000,
        risk_metadata={"density": "high", "shade_coverage": "low", "water_stress": "high"}
    )
    ward_repo.save_ward(w12)

    v12 = VulnerabilityProfile(
        ward_id="ward_12",
        outdoor_worker_count=1200,
        elderly_count=3400,
        children_count=5100,
        high_risk_population=9700,
        vulnerability_score=8.9
    )
    vuln_repo.save_vulnerability(v12)

    res_repo.save_resource(Resource(
        resource_id="res_w12_cc_a",
        ward_id="ward_12",
        type="cooling_centre",
        name="Cooling Centre A (Community Hall)",
        capacity=300,
        availability=250,
        contact_owner="Ward 12 Community Admin (+91-9876543210)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w12_cc_b",
        ward_id="ward_12",
        type="cooling_centre",
        name="Cooling Centre B (Library Annex)",
        capacity=200,
        availability=180,
        contact_owner="Ward 12 NGO Volunteer (+91-9876543211)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w12_wp_1",
        ward_id="ward_12",
        type="water_point",
        name="Municipal Hydrant Point 1",
        capacity=500,
        availability=400,
        contact_owner="Delhi Jal Board Ward 12 (+91-9876543212)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w12_hc_1",
        ward_id="ward_12",
        type="health_centre",
        name="Primary Health Centre 12",
        capacity=150,
        availability=100,
        contact_owner="Health Officer Ward 12 (+91-9876543213)"
    ))

    # Heat Event for Ward 12: Temp 44°C, Humidity 58%, Heat Index 52°C, Severity CRITICAL
    sev12, hi12 = calculate_heat_risk(44.0, 58.0)
    event_12 = HeatEvent(
        event_id="evt_w12_001",
        ward_id="ward_12",
        timestamp=now,
        temperature=44.0,
        humidity=58.0,
        heat_index=hi12,
        severity=sev12,
        duration=4
    )
    event_repo.save_event(event_12)

    # -------------------------------------------------------------
    # WARD 18 (High Risk Ward)
    # -------------------------------------------------------------
    w18 = Ward(
        ward_id="ward_18",
        name="Ward 18 — Lajpat Nagar West",
        city="Delhi",
        population=38000,
        risk_metadata={"density": "medium", "shade_coverage": "medium"}
    )
    ward_repo.save_ward(w18)

    v18 = VulnerabilityProfile(
        ward_id="ward_18",
        outdoor_worker_count=800,
        elderly_count=2900,
        children_count=4200,
        high_risk_population=7900,
        vulnerability_score=7.2
    )
    vuln_repo.save_vulnerability(v18)

    res_repo.save_resource(Resource(
        resource_id="res_w18_cc_1",
        ward_id="ward_18",
        type="cooling_centre",
        name="Lajpat Community Cooling Center",
        capacity=250,
        availability=200,
        contact_owner="Ward 18 Admin (+91-9876543220)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w18_hc_1",
        ward_id="ward_18",
        type="health_centre",
        name="Lajpat PolyClinic",
        capacity=120,
        availability=90,
        contact_owner="Health Officer Ward 18 (+91-9876543221)"
    ))

    sev18, hi18 = calculate_heat_risk(41.0, 45.0)
    event_18 = HeatEvent(
        event_id="evt_w18_001",
        ward_id="ward_18",
        timestamp=now - timedelta(minutes=30),
        temperature=41.0,
        humidity=45.0,
        heat_index=hi18,
        severity=sev18,
        duration=3
    )
    event_repo.save_event(event_18)

    # -------------------------------------------------------------
    # WARD 25 (Moderate Risk Ward)
    # -------------------------------------------------------------
    w25 = Ward(
        ward_id="ward_25",
        name="Ward 25 — Vasant Kunj Sector C",
        city="Delhi",
        population=30000,
        risk_metadata={"density": "low", "shade_coverage": "high"}
    )
    ward_repo.save_ward(w25)

    v25 = VulnerabilityProfile(
        ward_id="ward_25",
        outdoor_worker_count=350,
        elderly_count=2100,
        children_count=3100,
        high_risk_population=5550,
        vulnerability_score=4.5
    )
    vuln_repo.save_vulnerability(v25)

    res_repo.save_resource(Resource(
        resource_id="res_w25_cc_1",
        ward_id="ward_25",
        type="cooling_centre",
        name="Vasant Kunj Sports Complex",
        capacity=400,
        availability=350,
        contact_owner="Ward 25 Admin (+91-9876543230)"
    ))

    sev25, hi25 = calculate_heat_risk(37.0, 40.0)
    event_25 = HeatEvent(
        event_id="evt_w25_001",
        ward_id="ward_25",
        timestamp=now - timedelta(hours=1),
        temperature=37.0,
        humidity=40.0,
        heat_index=hi25,
        severity=sev25,
        duration=2
    )
    event_repo.save_event(event_25)

    # -------------------------------------------------------------
    # WARD 31 (Low Risk Ward)
    # -------------------------------------------------------------
    w31 = Ward(
        ward_id="ward_31",
        name="Ward 31 — Civil Lines Green Belt",
        city="Delhi",
        population=22000,
        risk_metadata={"density": "low", "shade_coverage": "high", "water_stress": "low"}
    )
    ward_repo.save_ward(w31)

    v31 = VulnerabilityProfile(
        ward_id="ward_31",
        outdoor_worker_count=120,
        elderly_count=650,
        children_count=1400,
        high_risk_population=2170,
        vulnerability_score=2.6
    )
    vuln_repo.save_vulnerability(v31)

    res_repo.save_resource(Resource(
        resource_id="res_w31_cc_1",
        ward_id="ward_31",
        type="cooling_centre",
        name="Civil Lines Community Room",
        capacity=300,
        availability=280,
        contact_owner="Ward 31 Admin (+91-9876543240)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w31_wp_1",
        ward_id="ward_31",
        type="water_point",
        name="Civil Lines Water Point 1",
        capacity=300,
        availability=280,
        contact_owner="Delhi Jal Board Ward 31 (+91-9876543241)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w31_wp_2",
        ward_id="ward_31",
        type="water_point",
        name="Civil Lines Water Point 2",
        capacity=250,
        availability=240,
        contact_owner="Delhi Jal Board Ward 31 (+91-9876543242)"
    ))
    res_repo.save_resource(Resource(
        resource_id="res_w31_hc_1",
        ward_id="ward_31",
        type="health_centre",
        name="Civil Lines Dispensary",
        capacity=80,
        availability=70,
        contact_owner="Health Officer Ward 31 (+91-9876543243)"
    ))

    sev31, hi31 = calculate_heat_risk(31.0, 35.0)
    event_31 = HeatEvent(
        event_id="evt_w31_001",
        ward_id="ward_31",
        timestamp=now - timedelta(hours=2),
        temperature=31.0,
        humidity=35.0,
        heat_index=hi31,
        severity=sev31,
        duration=1
    )
    event_repo.save_event(event_31)

    print("✅ Fresh demo data seeded (plans and tasks reset).")


if __name__ == "__main__":
    seed_demo_data(reset=True)
