from app.logic.skill_match import rank_technicians


def test_rank_technicians_prefers_full_coverage() -> None:
    ranked = rank_technicians(
        required={"hvac", "electrical"},
        candidates=[
            {"id": "t1", "skills": {"hvac"}, "travel_minutes": 10},
            {"id": "t2", "skills": {"hvac", "electrical"}, "travel_minutes": 25},
            {"id": "t3", "skills": {"plumbing"}, "travel_minutes": 5},
        ],
    )
    assert ranked[0]["id"] == "t2"
