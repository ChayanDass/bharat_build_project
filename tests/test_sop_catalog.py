from backend.agent.sop_catalog import select_sops


def test_critical_sops_are_department_specific_and_conditioned():
    sops = select_sops(
        severity="CRITICAL",
        outdoor_workers=1200,
        elderly=3400,
        children=5100,
        vulnerability_score=8.9,
        has_water_gap=True,
        has_cooling_gap=True,
    )

    by_id = {sop["sop_id"]: sop for sop in sops}

    assert set(by_id) == {
        "WD-01", "WD-03", "WD-04",
        "LD-01", "LD-03", "LD-04",
        "WO-01", "WO-03", "WO-04", "WO-06", "WO-07", "WO-08",
        "HD-01", "HD-02", "HD-04", "HD-05", "HD-06", "HD-07",
    }
    assert by_id["WD-01"]["team"] == "Water Dept"
    assert by_id["LD-01"]["team"] == "Labour Dept"
    assert by_id["WO-01"]["team"] == "Ward Officers"
    assert by_id["HD-01"]["team"] == "Health Dept"
    assert by_id["WO-08"]["team"] == "Ward Officers"
    assert by_id["HD-04"]["team"] == "Health Dept"


def test_water_tanker_requires_water_gap():
    sops = select_sops(
        severity="CRITICAL",
        outdoor_workers=1200,
        elderly=3400,
        vulnerability_score=8.9,
        has_water_gap=False,
    )

    selected_ids = {sop["sop_id"] for sop in sops}
    assert "WD-01" not in selected_ids
    assert "WD-04" not in selected_ids


def test_high_sops_use_scaled_down_preapproved_actions():
    sops = select_sops(
        severity="HIGH",
        outdoor_workers=800,
        elderly=2900,
        children=4200,
        has_water_gap=True,
        has_cooling_gap=True,
    )

    by_id = {sop["sop_id"]: sop for sop in sops}

    assert set(by_id) == {
        "WD-02", "WD-03",
        "LD-02", "LD-03",
        "WO-02", "WO-03", "WO-04", "WO-06", "WO-07", "WO-08",
        "HD-03", "HD-05", "HD-06", "HD-07",
    }
    assert by_id["WO-02"]["action"].startswith("Open Cooling Centre B as voluntary")
    assert by_id["LD-02"]["team"] == "Labour Dept"


def test_gap_specific_sops_do_not_fire_without_matching_gap():
    sops = select_sops(
        severity="HIGH",
        outdoor_workers=800,
        elderly=2900,
        children=4200,
        has_water_gap=False,
        has_cooling_gap=False,
    )

    selected_ids = {sop["sop_id"] for sop in sops}
    assert "WD-02" not in selected_ids
    assert "WO-06" not in selected_ids
    assert "WO-07" not in selected_ids
    assert "LD-02" in selected_ids
    assert "HD-05" in selected_ids


def test_moderate_response_uses_monitoring_and_precautionary_sops():
    sops = select_sops(
        severity="MODERATE",
        outdoor_workers=350,
        elderly=2100,
        children=3100,
    )

    by_id = {sop["sop_id"]: sop for sop in sops}
    assert set(by_id) == {"WD-05", "LD-05", "WO-04", "WO-05", "HD-03", "HD-07"}
    assert by_id["WD-05"]["team"] == "Water Dept"
    assert by_id["LD-05"]["team"] == "Labour Dept"
