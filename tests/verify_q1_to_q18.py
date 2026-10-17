import pytest
from datetime import datetime
from typing import Dict, Any, List

from backend.agent.tools import (
    tool_get_well_status_card,
    tool_query_non_producing_wells,
    tool_get_well_temperature_series,
    tool_query_spills,
    tool_get_spills_heatmap_2026,
    tool_calculate_downtime,
    tool_audit_well_compliance_and_rules,
    tool_record_user_feedback_or_correction,
    tool_get_my_private_conversation_memory
)
from backend.services.memory_engine import save_private_chat_message
from backend.services.conflict_engine import audit_spill_detection_validity, verify_user_claim
from backend.db.database import get_db_connection

def clean_runtime_state():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM data_corrections WHERE correction_id NOT LIKE 'CORR-CTX-%'")
    c.execute("DELETE FROM rule_overrides")
    c.execute("DELETE FROM private_chat_messages")
    c.execute("DELETE FROM private_chat_sessions")
    c.execute("DELETE FROM context_notes WHERE source = 'user'")
    conn.commit()
    conn.close()

@pytest.fixture(scope="module", autouse=True)
def setup_test_suite():
    clean_runtime_state()
    yield
    clean_runtime_state()

def test_q1_status_well_0001():
    """Q1: Is WELL-0001 producing oil right now? When was it last inspected, and by whom?"""
    res = tool_get_well_status_card("WELL-0001")
    assert res["visual_type"] == "card"
    data = res["data"]
    assert data["is_producing"] is False
    assert data["temp_delta_c"] == 3.2
    assert data["inspection_id"] == "INS-0001-0203"
    assert data["inspected_date"] == "2026-10-15"
    assert data["inspector_name"] == "Ryan Brooks"
    assert data["method"] == "drone"
    assert data["is_recorded_status_out_of_date"] is True
    assert "CTX-0001-003" in data["reason"] or "rod string" in data["reason"]

def test_q2_non_producing_northeast_block_8():
    """Q2: Which wells in Northeast Block 8 are not producing oil right now, and why?"""
    res = tool_query_non_producing_wells("Northeast Block 8")
    assert res["visual_type"] == "table"
    assert res["count"] == 4
    wells = {w["asset_id"]: w for w in res["data"]}
    assert set(wells.keys()) == {"WELL-0164", "WELL-0170", "WELL-0172", "WELL-0175"}
    
    # WELL-0164: no recorded reason, pump jack not moving note
    assert wells["WELL-0164"]["reason"] == "No recorded reason"
    assert "not moving" in wells["WELL-0164"]["inspector_notes"].lower()
    
    # WELL-0170: repair MNT-0170-031
    assert "MNT-0170-031" in wells["WELL-0170"]["reason"]
    
    # WELL-0172: repair MNT-0172-028
    assert "MNT-0172-028" in wells["WELL-0172"]["reason"]
    
    # WELL-0175: no recorded reason
    assert wells["WELL-0175"]["reason"] == "No recorded reason"

def test_q3_well_0001_temperature_series():
    """Q3: Line chart of WELL-0001 for last 13 weeks with non-producing flags."""
    res = tool_get_well_temperature_series("WELL-0001", last_n_weeks=13)
    assert res["visual_type"] == "line_chart"
    series = res["data"]
    assert len(series) == 13
    assert series[0]["inspected_date"] == "2026-07-23"
    assert series[-1]["inspected_date"] == "2026-10-15"
    
    non_prod_dates = [s["inspected_date"] for s in series if not s["is_producing"]]
    assert non_prod_dates == ["2026-10-08", "2026-10-15"]

def test_q4_spills_well_0001_4years():
    """Q4: How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total?"""
    res = tool_query_spills(asset_id="WELL-0001", start_date="2022-10-17", end_date="2026-10-17")
    assert res["visual_type"] == "table"
    assert res["spill_count"] == 6
    assert res["total_volume_bbl"] == 15.1
    assert len(res["excluded_false_positives"]) == 1
    assert res["excluded_false_positives"][0]["inspection_id"] == "INS-0001-0070"
    
    dates = [s["inspected_date"] for s in res["spills"]]
    vols = [s["spill_est_volume_bbl"] for s in res["spills"]]
    assert vols == [0.5, 2.6, 3.3, 0.3, 6.8, 1.6]

def test_q5_downtime_well_0001_2025():
    """Q5: How many days was WELL-0001 down in 2025?"""
    res = tool_calculate_downtime(asset_id="WELL-0001", start_date="2025-01-01", end_date="2025-12-31")
    assert res["visual_type"] == "none"
    assert res["downtime_days"] == 21
    assert res["non_producing_count"] == 3
    dates = [insp["inspected_date"] for insp in res["inspections"]]
    assert dates == ["2025-07-24", "2025-10-16", "2025-10-23"]

def test_q6_top_downtime_northeast_block_7():
    """Q6: Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months?"""
    res = tool_calculate_downtime(area_name_or_id="Northeast Block 7", start_date="2026-06-16", end_date="2026-10-16", top_k=3)
    assert res["visual_type"] == "bar_chart"
    top_wells = res["data"]
    top_ids = {w["asset_id"]: w["downtime_days"] for w in top_wells}
    assert top_ids["WELL-0121"] == 49
    assert top_ids["WELL-0138"] == 42
    assert top_ids["WELL-0107"] == 42

def test_q7_spills_map_northeast_block_8_90days():
    """Q7: Map of every well in Northeast Block 8 with a real spill in the last 90 days."""
    res = tool_query_spills(area_name_or_id="Northeast Block 8", start_date="2026-07-19", end_date="2026-10-17", as_map=True)
    assert res["visual_type"] == "map"
    assert res["spill_count"] == 4
    spill_dict = {s["asset_id"]: s for s in res["spills"]}
    assert set(spill_dict.keys()) == {"WELL-0151", "WELL-0165", "WELL-0175", "WELL-0186"}
    assert spill_dict["WELL-0151"]["spill_est_volume_bbl"] == 4.5
    assert spill_dict["WELL-0165"]["spill_est_volume_bbl"] == 1.2
    assert spill_dict["WELL-0175"]["spill_est_volume_bbl"] == 3.9
    assert spill_dict["WELL-0186"]["spill_est_volume_bbl"] == 0.6

def test_q8_spills_heatmap_2026():
    """Q8: Show a heatmap of 2026 spills by geographic area and month."""
    res = tool_get_spills_heatmap_2026(year=2026)
    assert res["visual_type"] == "heatmap"
    m = res["matrix"]
    assert m["Southwest Block 23"]["Total"] == 35
    assert m["Southwest Block 24"]["Total"] == 43
    assert m["Northeast Block 7"]["Total"] == 37
    assert m["Northeast Block 8"]["Total"] == 26

def test_q9_broken_rules_well_0001():
    """Q9: Which rules has WELL-0001 broken in the last 12 months, and what is still open?"""
    res = tool_audit_well_compliance_and_rules(asset_id="WELL-0001")
    assert res["visual_type"] == "table"
    breaches = {b["protocol"]: b for b in res["breaches"]}
    assert set(breaches.keys()) == {"SR-01", "SR-02", "SR-03", "RC-04"}
    
    # Check pending actions: RCA due on flowline & planned shut-in unrecorded
    pending_types = {p["type"] for p in res["pending_actions"]}
    assert "RCA Due" in pending_types
    assert "Planned Shut-in Unrecorded" in pending_types

def test_q10_late_containment_southwest_block_24():
    """Q10: In Southwest Block 24, which spills in the last 90 days were not contained within SOP limit?"""
    res = tool_query_spills(area_name_or_id="Southwest Block 24", start_date="2026-07-19", end_date="2026-10-17", only_late_containment=True)
    assert res["visual_type"] == "table"
    assert res["spill_count"] == 2
    spill_ids = [s["asset_id"] for s in res["spills"]]
    assert spill_ids == ["WELL-0082", "WELL-0100"]
    assert res["spills"][0]["containment_hours"] == 7.1
    assert res["spills"][1]["containment_hours"] == 8.1

def test_q11_memory_recall_and_repair_costs():
    """Q11: Day 2 new chat: Michael Turner asks for 2026 repair costs of the three wells discussed yesterday."""
    # Seed Day 1 conversation for Michael Turner (U-201)
    session_1 = "turner-session-1"
    save_private_chat_message(
        session_id=session_1,
        user_id="U-201",
        role="assistant",
        content="The top 3 downtime wells are WELL-0121, WELL-0138, and WELL-0107.",
        entities_discussed=["WELL-0121", "WELL-0138", "WELL-0107"]
    )
    
    # Day 2 query by Michael Turner
    mem = tool_get_my_private_conversation_memory(user_id="U-201", query_well_costs_year=2026)
    assert mem["has_prior_context"] is True
    costs = mem["costs"]["well_costs"]
    assert costs["WELL-0121"] == 25794
    assert costs["WELL-0138"] == 46942
    assert costs["WELL-0107"] == 5176

def test_q12_raw_data_correction_and_reask():
    """Q12: Michael Turner corrects WELL-0164 temp to 41.0 °C, flags conflict, and re-asks Q2."""
    rec = tool_record_user_feedback_or_correction(
        user_id="U-201",
        feedback_type="raw_data_correction",
        asset_id="WELL-0164",
        inspection_id="INS-0164-0205",
        field_name="wellhead_temp_c",
        new_value=41.0,
        reason="The handheld thermal gun used was faulty; field crew re-measured wellhead at 41.0 °C"
    )
    assert rec["status"] == "success"
    assert "Warning" in rec["conflict_warning"]
    assert "not moving" in rec["conflict_warning"].lower()
    
    # Re-ask Q2: Northeast Block 8 non-producing wells now returns 3 wells (WELL-0164 is producing!)
    q2_reask = tool_query_non_producing_wells("Northeast Block 8")
    assert q2_reask["count"] == 3
    reask_ids = [w["asset_id"] for w in q2_reask["data"]]
    assert reask_ids == ["WELL-0170", "WELL-0172", "WELL-0175"]
    assert "WELL-0164" not in reask_ids

def test_q13_ai_spill_volume_correction():
    """Q13: Michael Turner corrects WELL-0151 spill from 4.5 to 5.4 bbl, triggering reportable status."""
    rec = tool_record_user_feedback_or_correction(
        user_id="U-201",
        feedback_type="spill_volume_correction",
        asset_id="WELL-0151",
        inspection_id="INS-0151-0201",
        new_value=5.4,
        reason="Field crew measured 5.4 bbl"
    )
    assert rec["status"] == "success"
    assert rec["is_reportable"] is True
    assert "SR-01" in rec["regulatory_implications"]
    assert "SR-03" in rec["regulatory_implications"]
    assert "23 Nov 2026" in rec["regulatory_implications"]

def test_q14_rule_override_well_type():
    """Q14: Michael Turner sets T350 pump jack RCA threshold to 2, adding WELL-0120 while keeping T200 wells excluded."""
    # Before rule: 3 wells
    before = tool_audit_well_compliance_and_rules(area_name_or_id="Northeast Block 7", equipment_kind_for_rca="pump_jack")
    assert [w["asset_id"] for w in before["wells"]] == ["WELL-0108", "WELL-0121", "WELL-0138"]
    
    # Set rule override: T350 pump_jack -> 2 repairs
    rule_res = tool_record_user_feedback_or_correction(
        user_id="U-201",
        feedback_type="rule_override",
        scope_well_type="T350",
        equipment_kind="pump_jack",
        new_value=2,
        reason="Our team now wants a pump jack root-cause analysis after 2 repairs, not 3"
    )
    assert rule_res["status"] == "success"
    
    # Re-query: WELL-0120 (T350 with 2 repairs) is added, WELL-0102 (T200 with 2 repairs) is NOT added!
    after = tool_audit_well_compliance_and_rules(area_name_or_id="Northeast Block 7", equipment_kind_for_rca="pump_jack")
    after_ids = [w["asset_id"] for w in after["wells"]]
    assert after_ids == ["WELL-0108", "WELL-0120", "WELL-0121", "WELL-0138"]
    assert "WELL-0102" not in after_ids

def test_q15_corrections_reach_other_users():
    """Q15: Jessica Reed checks WELL-0164 (gets producing=True); Laura Simmons checks NE-08 reportable spills (gets WELL-0151)."""
    # Jessica Reed checks WELL-0164
    reed_card = tool_get_well_status_card("WELL-0164")
    assert reed_card["data"]["is_producing"] is True
    assert reed_card["data"]["eff_wellhead_temp_c"] == 41.0
    
    # Laura Simmons checks spills in Northeast Block 8 in last 90 days needing report
    spills_sim = tool_query_spills(area_name_or_id="Northeast Block 8", start_date="2026-07-19", end_date="2026-10-17", only_reportable=True)
    assert spills_sim["spill_count"] == 1
    assert spills_sim["spills"][0]["asset_id"] == "WELL-0151"
    assert spills_sim["spills"][0]["spill_est_volume_bbl"] == 5.4

def test_q16_shared_knowledge_and_strict_privacy_isolation():
    """Q16: Morales logs planned shut-in -> Turner sees it -> Reed asks about Q11 memory and is refused."""
    # Jake Morales logs planned workover on WELL-0007
    note_res = tool_record_user_feedback_or_correction(
        user_id="U-102",
        feedback_type="operational_note",
        asset_id="WELL-0007",
        reason="WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.",
        valid_from="2026-10-17",
        valid_to="2026-10-27"
    )
    assert note_res["status"] == "success"
    
    # Michael Turner queries WELL-0007
    well_7 = tool_get_well_status_card("WELL-0007")
    assert "10-day planned workover" in well_7["data"]["reason"] or "WELL-0007" in well_7["data"]["reason"]
    
    # Jessica Reed asks for yesterday's discussed wells -> MUST BE REFUSED (isolated from Turner's session)
    reed_mem = tool_get_my_private_conversation_memory(user_id="U-202")
    assert reed_mem["has_prior_context"] is False
    assert "No earlier conversation" in reed_mem["message"]

def test_q17_conflicting_user_claims_vs_data():
    """Q17: Tyler Hughes claims WELL-0175 is running fine; Jake Morales claims WELL-0001 is back online."""
    # Michael Turner note: WELL-0175 shut in since 14 Oct
    tool_record_user_feedback_or_correction(
        user_id="U-201",
        feedback_type="operational_note",
        asset_id="WELL-0175",
        reason="WELL-0175 has been shut in for planned work since 14 Oct.",
        valid_from="2026-10-14"
    )
    
    # Tyler Hughes claims "WELL-0175 is running fine"
    hughes_claim = tool_record_user_feedback_or_correction(
        user_id="U-204",
        feedback_type="user_claim",
        asset_id="WELL-0175",
        claim_text="WELL-0175 is running fine."
    )
    assert hughes_claim["verification"]["has_conflict"] is True
    assert hughes_claim["verification"]["status"] == "unconfirmed"
    assert "0.4" in hughes_claim["message"] or "not producing" in hughes_claim["message"]
    
    # Jake Morales claims "WELL-0001 is back online since 14 Oct"
    morales_claim = tool_record_user_feedback_or_correction(
        user_id="U-102",
        feedback_type="user_claim",
        asset_id="WELL-0001",
        claim_text="WELL-0001 is back online since 14 Oct."
    )
    assert morales_claim["verification"]["has_conflict"] is True
    assert morales_claim["verification"]["status"] == "unconfirmed"
    assert "3.2" in morales_claim["message"] or "not producing" in morales_claim["message"]

def test_q18_disagreement_about_detection():
    """Q18: Was the 20 Aug spill at WELL-0101 real oil?"""
    res = audit_spill_detection_validity("WELL-0101", "INS-0101-0197")
    assert res["is_real_oil"] is True
    assert res["has_conflicting_notes"] is True
    assert len(res["notes_detail"]) >= 2
    assert "stands" in res["conclusion"]
    assert res["maintenance_completed"] == "MNT-0101-029"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
