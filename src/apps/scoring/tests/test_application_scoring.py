import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.apps.scoring.services.scoring_service import ApplicationScoringService


def _make_profile(licence_averages=(12.0, 14.0, 16.0), m1_moyenne=None, nb_redoublements=0):
    licence_years = [SimpleNamespace(moyenne=avg) for avg in licence_averages]
    m1_year = SimpleNamespace(moyenne=m1_moyenne) if m1_moyenne is not None else None
    redoublement = SimpleNamespace(
        a_redouble=nb_redoublements > 0,
        redoublement_years=SimpleNamespace(count=lambda: nb_redoublements),
    )

    profile = SimpleNamespace(
        id=1,
        pk=1,
        licence_years=SimpleNamespace(all=lambda: licence_years),
        master1_year=m1_year,
        redoublement=redoublement,
    )
    return profile


def test_standard_scoring_licence_only():
    profile = _make_profile(licence_averages=[12.0, 14.0, 16.0], m1_moyenne=None, nb_redoublements=0)
    master = SimpleNamespace(id=1, score_formula=None)

    # Average = (12 + 14 + 16) / 3 = 14.0
    score = ApplicationScoringService.calculate_score(profile, master)
    assert score == 14.0


def test_standard_scoring_with_master1():
    profile = _make_profile(licence_averages=[12.0, 14.0, 16.0], m1_moyenne=15.0, nb_redoublements=0)
    master = SimpleNamespace(id=1, score_formula=None)

    # Score = 14.0 * 0.6 + 15.0 * 0.4 = 8.4 + 6.0 = 14.40
    score = ApplicationScoringService.calculate_score(profile, master)
    assert score == 14.40


def test_standard_scoring_with_redoublement_malus():
    profile = _make_profile(licence_averages=[12.0, 14.0, 16.0], m1_moyenne=15.0, nb_redoublements=2)
    master = SimpleNamespace(id=1, score_formula=None)

    # Score = 14.40 - (0.5 * 2) = 13.40
    score = ApplicationScoringService.calculate_score(profile, master)
    assert score == 13.40


def test_scoring_bounded_to_zero():
    profile = _make_profile(licence_averages=[5.0, 5.0, 5.0], m1_moyenne=None, nb_redoublements=15)
    master = SimpleNamespace(id=1, score_formula=None)

    score = ApplicationScoringService.calculate_score(profile, master)
    assert score == 0.0
