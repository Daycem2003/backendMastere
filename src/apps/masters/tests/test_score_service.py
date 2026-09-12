from types import SimpleNamespace

from src.apps.masters.services.score_service import ScoreService


def _formula(criteria):
    return SimpleNamespace(criteria=SimpleNamespace(all=lambda: criteria))


def _criterion(critere, poids):
    return SimpleNamespace(critere=critere, poids=poids)


def test_compute_score_returns_none_when_no_formula():
    master = SimpleNamespace(score_formula=None)
    assert ScoreService.compute_score({"average": 15}, master) is None


def test_compute_score_returns_none_when_metric_missing():
    master = SimpleNamespace(score_formula=_formula([_criterion("average", 1.0)]))
    assert ScoreService.compute_score({}, master) is None


def test_compute_score_weighted_average():
    master = SimpleNamespace(
        score_formula=_formula([_criterion("average", 2.0), _criterion("interview", 1.0)])
    )
    score = ScoreService.compute_score({"average": 15, "interview": 12}, master)
    # (15*2 + 12*1) / (2+1) = 42/3 = 14
    assert score == 14.0


def test_compute_score_single_criterion_returns_raw_value():
    master = SimpleNamespace(score_formula=_formula([_criterion("average", 1.0)]))
    assert ScoreService.compute_score({"average": 16.5}, master) == 16.5
