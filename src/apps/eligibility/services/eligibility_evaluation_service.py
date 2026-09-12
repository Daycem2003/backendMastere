import logging
from datetime import date

from src.apps.eligibility.domain.candidate_snapshot import CandidateSnapshot
from src.apps.eligibility.domain.eligibility_result import EligibilityResult, FailedRule
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.models import EligibilityCriteria
from src.apps.eligibility.selectors.eligibility_selector import list_for_master

logger = logging.getLogger(__name__)


def _normalize_string(val: str | None) -> str:
    if val is None:
        return ""
    normalized = str(val).strip().lower()
    nationality_map = {
        "tunisienne": "tunisienne",
        "tunisien": "tunisienne",
        "tunisie": "tunisienne",
        "tn": "tunisienne",
    }
    return nationality_map.get(normalized, normalized)


class EligibilityService:
    """Moteur générique d'évaluation. Chaque `evaluate_*` est pur (aucun
    accès DB, aucun effet de bord) — testable indépendamment de l'ORM,
    comme demandé (section 12 : "code testable")."""

    @staticmethod
    def evaluate(snapshot: CandidateSnapshot, master) -> EligibilityResult:
        """Étape 1 (section 6) : type de licence accepté par le master —
        condition implicite, pas stockée comme `EligibilityCriteria`
        (relation M2M dédiée `Master.type_licences_acceptees`).
        Étape 2 : toutes les règles génériques du master, cumulatives (AND).
        """
        failed: list[FailedRule] = []

        if not EligibilityService._licence_type_accepted(snapshot, master):
            failed.append(
                FailedRule(
                    criterion="licence_type",
                    expected=", ".join(
                        t.intitule for t in master.type_licences_acceptees.all()
                    ) or "(aucun type accepté configuré)",
                    actual=snapshot.licence_type_name or snapshot.licence_type_code or "(non renseigné)",
                    reason="Le type de licence du candidat n'est pas accepté par ce master.",
                )
            )

        for criteria in list_for_master(master.pubkey):
            failure = EligibilityService.evaluate_rule(snapshot, criteria)
            if failure:
                failed.append(failure)

        return EligibilityResult(eligible=not failed, failed_rules=failed)

    @staticmethod
    def _licence_type_accepted(snapshot: CandidateSnapshot, master) -> bool:
        if not hasattr(master, "type_licences_acceptees"):
            return True
        tla = master.type_licences_acceptees
        if hasattr(tla, "exists") and not tla.exists():
            return True
        if hasattr(tla, "count") and tla.count() == 0:
            return True
        if hasattr(tla, "all"):
            all_tla = list(tla.all())
            if not all_tla:
                return True

        if snapshot.licence_type_code is None:
            return False

        if hasattr(tla, "values_list"):
            accepted_codes = set(tla.values_list("pubkey", flat=True))
            if snapshot.licence_type_code in accepted_codes:
                return True
            accepted_pks = set(str(pk) for pk in tla.values_list("pk", flat=True))
            if str(snapshot.licence_type_code) in accepted_pks:
                return True
        if hasattr(tla, "all"):
            for t in tla.all():
                if getattr(t, "pubkey", None) == snapshot.licence_type_code or str(getattr(t, "pk", "")) == str(snapshot.licence_type_code):
                    return True
        return False

    @staticmethod
    def evaluate_rule(snapshot: CandidateSnapshot, criteria: EligibilityCriteria) -> FailedRule | None:
        """Retourne un `FailedRule` si le critère échoue, `None` s'il
        passe. Un critère non `obligatoire` qui échoue par absence de
        donnée (pas par violation) n'est pas bloquant (voir chaque
        evaluate_* pour la distinction "donnée manquante" vs "échec")."""
        rule = criteria.rule_value
        actual_value = getattr(snapshot, criteria.criterion, None)

        if actual_value is None:
            if criteria.obligatoire:
                return FailedRule(
                    criterion=criteria.criterion,
                    expected=EligibilityService._describe_expected(rule),
                    actual="(non renseigné)",
                    reason=f"Donnée requise manquante pour le critère '{criteria.criterion}'.",
                )
            return None  # facultatif et non renseigné -> ne bloque pas

        dispatch = {
            ValueType.NUMERIC: EligibilityService.evaluate_numeric,
            ValueType.NUMERIC_RANGE: EligibilityService.evaluate_numeric_range,
            ValueType.DATE: EligibilityService.evaluate_date,
            ValueType.DATE_RANGE: EligibilityService.evaluate_date_range,
            ValueType.STRING: EligibilityService.evaluate_string,
            ValueType.ENUM: EligibilityService.evaluate_string,
            ValueType.BOOLEAN: EligibilityService.evaluate_boolean,
        }
        evaluator = dispatch[rule.value_type]
        passed = evaluator(actual_value, rule)
        if passed:
            return None

        return FailedRule(
            criterion=criteria.criterion,
            expected=EligibilityService._describe_expected(rule),
            actual=str(actual_value),
            reason=f"La valeur pour '{criteria.criterion}' ne respecte pas la règle configurée.",
        )

    # --- Évaluateurs purs, un par type de valeur ------------------------

    @staticmethod
    def evaluate_numeric(actual: float, rule) -> bool:
        try:
            act = float(actual)
            exp = float(rule.value)
        except (ValueError, TypeError):
            return False

        eps = 1e-5
        ops = {
            Operator.EQ: lambda a, b: abs(a - b) < eps,
            Operator.NEQ: lambda a, b: abs(a - b) >= eps,
            Operator.GT: lambda a, b: a > (b + eps),
            Operator.GTE: lambda a, b: a >= (b - eps),
            Operator.LT: lambda a, b: a < (b - eps),
            Operator.LTE: lambda a, b: a <= (b + eps),
        }
        if rule.operator not in ops:
            return False
        return ops[rule.operator](act, exp)

    @staticmethod
    def evaluate_numeric_range(actual: float, rule) -> bool:
        try:
            act = float(actual)
        except (ValueError, TypeError):
            return False

        eps = 1e-5
        if rule.min_value is not None:
            try:
                min_val = float(rule.min_value)
                min_ok = act >= (min_val - eps) if rule.min_inclusive else act > (min_val + eps)
                if not min_ok:
                    return False
            except (ValueError, TypeError):
                return False
        if rule.max_value is not None:
            try:
                max_val = float(rule.max_value)
                max_ok = act <= (max_val + eps) if rule.max_inclusive else act < (max_val - eps)
                if not max_ok:
                    return False
            except (ValueError, TypeError):
                return False
        return True

    @staticmethod
    def evaluate_date(actual: date, rule) -> bool:
        expected = date.fromisoformat(str(rule.value))
        ops = {
            Operator.EQ: lambda a, b: a == b,
            Operator.NEQ: lambda a, b: a != b,
            Operator.GT: lambda a, b: a > b,
            Operator.GTE: lambda a, b: a >= b,
            Operator.LT: lambda a, b: a < b,
            Operator.LTE: lambda a, b: a <= b,
        }
        return ops[rule.operator](actual, expected)

    @staticmethod
    def evaluate_date_range(actual: date, rule) -> bool:
        if rule.min_value is not None:
            min_date = date.fromisoformat(str(rule.min_value))
            min_ok = actual >= min_date if rule.min_inclusive else actual > min_date
            if not min_ok:
                return False
        if rule.max_value is not None:
            max_date = date.fromisoformat(str(rule.max_value))
            max_ok = actual <= max_date if rule.max_inclusive else actual < max_date
            if not max_ok:
                return False
        return True

    @staticmethod
    def evaluate_string(actual: str, rule) -> bool:
        """Sert aussi ENUM (même logique : égalité ou appartenance à une
        liste) et couvre nationalité / nom d'université de la spec, sans
        colonne dédiée par type de critère."""
        norm_actual = _normalize_string(actual)
        if rule.operator == Operator.EQ:
            return norm_actual == _normalize_string(rule.value)
        if rule.operator == Operator.NEQ:
            return norm_actual != _normalize_string(rule.value)
        if rule.operator == Operator.IN:
            norm_values = [_normalize_string(v) for v in (rule.values or [])]
            return norm_actual in norm_values
        if rule.operator == Operator.NOT_IN:
            norm_values = [_normalize_string(v) for v in (rule.values or [])]
            return norm_actual not in norm_values
        return False

    @staticmethod
    def evaluate_boolean(actual: bool, rule) -> bool:
        if rule.operator == Operator.EQ:
            return actual == rule.value
        if rule.operator == Operator.NEQ:
            return actual != rule.value
        return False

    @staticmethod
    def _describe_expected(rule) -> str:
        if rule.value_type in (ValueType.NUMERIC_RANGE, ValueType.DATE_RANGE):
            lo = f"{'[' if rule.min_inclusive else ']'}{rule.min_value}" if rule.min_value is not None else "(-∞"
            hi = f"{rule.max_value}{']' if rule.max_inclusive else '['}" if rule.max_value is not None else "+∞)"
            return f"{lo}, {hi}"
        if rule.operator in (Operator.IN, Operator.NOT_IN):
            return f"{rule.operator.value} {rule.values}"
        return f"{rule.operator.value} {rule.value}"
