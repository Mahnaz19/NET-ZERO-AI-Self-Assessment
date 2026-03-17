from __future__ import annotations

from backend.reportgen.render import render_report_html


def test_render_report_html_includes_standard_fields():
    report_json = {
        "executive_summary": "Summary text",
        "baseline": {
            "annual_kwh": 10000,
            "annual_cost_gbp": 3000,
            "tariff_p_per_kwh": 30,
            "annual_co2_tonnes": 2.33,
        },
        "recommendations": [
            {
                "measure_code": "LED_UPGRADE",
                "recommendation_text": "Upgrade to LEDs",
                "priority": 1,
                "confidence": "High",
                "estimated_annual_kwh_saved": 1000.0,
                "estimated_annual_saving_gbp": 300.0,
                "estimated_implementation_cost_gbp": 5000.0,
                "payback_years": 3.0,
                "estimated_annual_co2_saved_tonnes": 0.25,
            }
        ],
    }

    html = render_report_html(report_json)

    # Headings
    assert "Annual kWh saved" in html
    assert "Annual saving (GBP)" in html
    assert "Implementation cost (GBP)" in html
    assert "Payback (years)" in html
    assert "Annual CO₂ saved (tonnes)" in html

    # Numeric values rendered
    assert "1000.0" in html
    assert "300.0" in html
    assert "5000.0" in html
    assert "3.0" in html
    assert "0.25" in html

