import pandas as pd
import pytest

from joblens.stats import compare, wilson_interval


def test_wilson_interval() -> None:
    lower, upper = wilson_interval(6, 10)
    assert lower == pytest.approx(0.313, abs=0.001)
    assert upper == pytest.approx(0.832, abs=0.001)


def test_compare_uses_fisher_and_corrects_zero_cells() -> None:
    postings = pd.DataFrame(
        {
            "country": ["A", "A", "A", "B", "B", "B"],
            "skills": [["SQL"], ["SQL"], [], [], [], []],
        }
    )

    result = compare(postings, "country")
    group_a = result[result["group"] == "A"].iloc[0]
    assert group_a["skill"] == "SQL"
    assert group_a["method"] == "Fisher exact"
    assert group_a["group_n"] == 3
    assert group_a["other_n"] == 3
    assert group_a["odds_ratio"] == pytest.approx(11.6667, rel=0.001)
    assert bool(group_a["small_sample"])


def test_compare_bh_adjustment_can_exceed_raw_p_value() -> None:
    postings = pd.DataFrame(
        {
            "country": ["A"] * 4 + ["B"] * 4,
            "skills": [
                ["strong"],
                ["strong"],
                ["strong"],
                ["strong", "balanced"],
                ["balanced"],
                ["balanced"],
                ["rare"],
                ["rare"],
            ],
        }
    )

    result = compare(postings, "country")
    assert (result["p_adjusted"] >= result["p_value"]).all()
    assert (result["p_adjusted"] > result["p_value"]).any()
