from backend.services.truth_engine import (
    get_well_latest_status,
    get_non_producing_wells_in_area,
    query_spills,
    calculate_well_downtime,
    calculate_area_top_downtime,
    get_spills_heatmap_2026
)
from backend.services.compliance_engine import audit_well_compliance, get_wells_needing_rca

def run_tests():
    print("--- Q1 Test (WELL-0001 status) ---")
    q1 = get_well_latest_status("WELL-0001")
    insp = q1["latest_inspection"]
    print(f"Producing: {insp['is_producing']}, Delta: {insp['temp_delta_c']}, Stale status: {insp['is_recorded_status_out_of_date']}")
    assert insp["is_producing"] is False
    assert insp["temp_delta_c"] == 3.2
    assert insp["is_recorded_status_out_of_date"] is True
    print("Q1 PASSED!")

    print("\n--- Q2 Test (NE-08 non-producing) ---")
    q2 = get_non_producing_wells_in_area("Northeast Block 8")
    for w in q2:
        print(w["asset_id"], w["temp_delta_c"], w["recorded_status"], w["reason"][:60])
    q2_ids = [w["asset_id"] for w in q2]
    assert q2_ids == ["WELL-0164", "WELL-0170", "WELL-0172", "WELL-0175"]
    print("Q2 PASSED!")

    print("\n--- Q4 Test (WELL-0001 spills 4y) ---")
    q4 = query_spills(asset_id="WELL-0001", start_date="2022-10-17", end_date="2026-10-17")
    print(f"Count: {q4['spill_count']}, Total Vol: {q4['total_volume_bbl']}, Excluded: {len(q4['excluded_false_positives'])}")
    assert q4["spill_count"] == 6
    assert q4["total_volume_bbl"] == 15.1
    assert len(q4["excluded_false_positives"]) == 1
    print("Q4 PASSED!")

    print("\n--- Q5 Test (WELL-0001 downtime 2025) ---")
    q5 = calculate_well_downtime("WELL-0001", "2025-01-01", "2025-12-31")
    print(f"Downtime days: {q5['downtime_days']}, Inspections: {q5['non_producing_count']}")
    assert q5["downtime_days"] == 21
    assert q5["non_producing_count"] == 3
    print("Q5 PASSED!")

    print("\n--- Q6 Test (NE-07 top downtime last 4m) ---")
    q6 = calculate_area_top_downtime("Northeast Block 7", "2026-06-16", "2026-10-16", top_k=4)
    for w in q6:
        print(w["asset_id"], w["well_type"], w["downtime_days"])
    top3_ids = {q6[0]["asset_id"], q6[1]["asset_id"], q6[2]["asset_id"]}
    assert top3_ids == {"WELL-0121", "WELL-0138", "WELL-0107"}
    assert q6[3]["asset_id"] == "WELL-0119" and q6[3]["downtime_days"] == 28
    print("Q6 PASSED!")

    print("\n--- Q8 Test (Heatmap 2026) ---")
    q8 = get_spills_heatmap_2026(2026)
    assert q8["matrix"]["Southwest Block 23"]["Total"] == 35
    assert q8["matrix"]["Southwest Block 24"]["Total"] == 43
    assert q8["matrix"]["Northeast Block 7"]["Total"] == 37
    assert q8["matrix"]["Northeast Block 8"]["Total"] == 26
    print("Q8 PASSED!")

    print("\n--- Q9 Test (WELL-0001 broken rules last 12m) ---")
    q9 = audit_well_compliance("WELL-0001")
    print(f"Breaches count: {len(q9['breaches'])}")
    for b in q9["breaches"]:
        print(f"  [{b['protocol']}] {b['description']}")
    for p in q9["pending_actions"]:
        print(f"  [Pending: {p['type']}] {p['description']}")
    for m in q9["rules_met"]:
        print(f"  [Met: {m['protocol']}] {m['description']}")
    protocols_broken = {b["protocol"] for b in q9["breaches"]}
    assert protocols_broken == {"SR-01", "SR-02", "SR-03", "RC-04"}
    print("Q9 PASSED!")

    print("\n--- Q10 Test (SW-24 spills late containment last 90d) ---")
    q10 = query_spills(area_name_or_id="Southwest Block 24", start_date="2026-07-19", end_date="2026-10-17", only_late_containment=True)
    print("Late containment spills in SW-24:", [(s["asset_id"], s["containment_hours"]) for s in q10["spills"]])
    assert [s["asset_id"] for s in q10["spills"]] == ["WELL-0082", "WELL-0100"]
    print("Q10 PASSED!")

    print("\n--- Q14 Initial Test (NE-07 pump jack RCA before rule) ---")
    q14_before = get_wells_needing_rca("Northeast Block 7", "pump_jack")
    q14_before_ids = [w["asset_id"] for w in q14_before]
    print("Before rule:", q14_before_ids)
    assert q14_before_ids == ["WELL-0108", "WELL-0121", "WELL-0138"]
    print("Q14 Initial PASSED!")

if __name__ == "__main__":
    run_tests()
