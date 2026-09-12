import logging
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.masters.models import Master

logger = logging.getLogger(__name__)


class ApplicationScoringService:
    """Service de calcul de score pour les candidatures aux Masters.

    Formule standard déterministe :
    - Si le candidat a validé une 1ère année de Master (M1) :
      Score = (Moyenne Licence * 0.6) + (Moyenne M1 * 0.4) - (0.5 * Nb Redoublements)
    - Sinon :
      Score = Moyenne Licence - (0.5 * Nb Redoublements)

    Si le Master a une formule personnalisée (ScoreFormula avec critères pondérés),
    celle-ci est évaluée prioritairement.
    Le score final est borné entre 0.0 et 20.0 et arrondi à 2 décimales.
    """

    @classmethod
    def calculate_score(cls, profile: CandidateProfile, master: Master) -> float:
        # 1. Calcul de la moyenne générale de licence
        licence_years = list(profile.licence_years.all())
        if licence_years:
            licence_avg = sum(float(ly.moyenne) for ly in licence_years) / len(licence_years)
        else:
            licence_avg = 10.0

        # 2. Moyenne de Master 1 si présente
        m1_year = getattr(profile, "master1_year", None)
        m1_avg = float(m1_year.moyenne) if (m1_year and m1_year.moyenne is not None) else None

        # 3. Malus de redoublement (0.5 point par année redoublée)
        redoublement = getattr(profile, "redoublement", None)
        nb_redoublements = (
            redoublement.redoublement_years.count()
            if (redoublement and redoublement.a_redouble)
            else 0
        )
        malus = 0.5 * nb_redoublements

        # 4. Vérification d'une formule personnalisée sur le Master
        score_formula = getattr(master, "score_formula", None)
        if score_formula and score_formula.criteria.exists():
            metrics = {
                "moyenne_licence": licence_avg,
                "moyenne_m1": m1_avg if m1_avg is not None else licence_avg,
                "redoublements": float(nb_redoublements),
            }
            total = 0.0
            total_weight = 0.0
            for crit in score_formula.criteria.all():
                val = metrics.get(crit.critere, 0.0)
                total += val * crit.poids
                total_weight += crit.poids
            if total_weight > 0:
                raw_score = total / total_weight - malus
                final_score = max(0.0, min(20.0, round(raw_score, 2)))
                logger.info(
                    "custom_score_calculated",
                    extra={"profile_id": profile.id, "master_id": master.id, "score": final_score},
                )
                return final_score

        # 5. Formule standard
        if m1_avg is not None:
            raw_score = (licence_avg * 0.6) + (m1_avg * 0.4) - malus
        else:
            raw_score = licence_avg - malus

        final_score = max(0.0, min(20.0, round(raw_score, 2)))
        logger.info(
            "standard_score_calculated",
            extra={"profile_id": profile.id, "master_id": master.id, "score": final_score},
        )
        return final_score
