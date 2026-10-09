import pytest
from backend.domain.services import calculate_heat_index, calculate_heat_risk
from backend.domain.models import HeatSeverity


def test_calculate_heat_index():
    # 44°C and 58% humidity should produce a high heat index (~52°C)
    hi = calculate_heat_index(44.0, 58.0)
    assert hi >= 50.0


def test_calculate_heat_risk_critical():
    severity, hi = calculate_heat_risk(44.0, 58.0)
    assert severity == HeatSeverity.CRITICAL
    assert hi >= 50.0


def test_calculate_heat_risk_high():
    # 40°C with 25% humidity gives Heat Index ~42°C (HIGH)
    severity, hi = calculate_heat_risk(40.0, 25.0)
    assert severity == HeatSeverity.HIGH


def test_calculate_heat_risk_moderate():
    # 36°C with 30% humidity gives Heat Index ~38°C (MODERATE)
    severity, hi = calculate_heat_risk(36.0, 30.0)
    assert severity == HeatSeverity.MODERATE


def test_calculate_heat_risk_low():
    severity, hi = calculate_heat_risk(30.0, 30.0)
    assert severity == HeatSeverity.LOW
