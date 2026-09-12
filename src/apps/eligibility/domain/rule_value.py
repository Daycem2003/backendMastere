import json
from datetime import date

from pydantic import BaseModel, model_validator

from src.apps.eligibility.domain.value_types import VALID_OPERATORS_BY_TYPE, Operator, ValueType


class RuleValueData(BaseModel):
    """Structure générique d'une règle d'éligibilité — sérialisée en JSON
    dans la colonne legacy `MST_ELIGIBILITY_CRITERIA.valeur` (voir
    `eligibility/models.py` pour la justification de ce choix).

    Un seul de ces jeux de champs est rempli selon `value_type` :
    - NUMERIC / DATE / STRING / ENUM / BOOLEAN -> `operator` + `value`
    - NUMERIC_RANGE / DATE_RANGE -> `min_value` / `max_value` (+ bornes)
    """

    value_type: ValueType
    operator: Operator | None = None
    value: float | str | bool | None = None
    values: list[str] | None = None  # pour IN / NOT_IN
    min_value: float | str | None = None
    max_value: float | str | None = None
    min_inclusive: bool = True
    max_inclusive: bool = True

    @model_validator(mode="after")
    def validate_coherence(self) -> "RuleValueData":
        is_range = self.value_type in (ValueType.NUMERIC_RANGE, ValueType.DATE_RANGE)

        if is_range:
            if self.min_value is None and self.max_value is None:
                raise ValueError(
                    f"{self.value_type.value} nécessite au moins min_value ou max_value."
                )
            if self.min_value is not None and self.max_value is not None:
                if self.value_type == ValueType.NUMERIC_RANGE and float(self.min_value) > float(self.max_value):
                    raise ValueError("min_value doit être <= max_value pour NUMERIC_RANGE.")
                if self.value_type == ValueType.DATE_RANGE:
                    self._validate_date(self.min_value)
                    self._validate_date(self.max_value)
                    if date.fromisoformat(str(self.min_value)) > date.fromisoformat(str(self.max_value)):
                        raise ValueError("date_from doit être <= date_to pour DATE_RANGE.")
            return self

        # Types non-range : un opérateur est requis, cohérent avec le type.
        if self.operator is None:
            raise ValueError(f"{self.value_type.value} nécessite un opérateur.")
        allowed = VALID_OPERATORS_BY_TYPE.get(self.value_type, set())
        if self.operator not in allowed:
            raise ValueError(
                f"Opérateur {self.operator.value} invalide pour le type {self.value_type.value} "
                f"(autorisés : {[o.value for o in allowed]})."
            )

        if self.operator in (Operator.IN, Operator.NOT_IN):
            if not self.values:
                raise ValueError(f"L'opérateur {self.operator.value} nécessite une liste `values` non vide.")
        else:
            if self.value is None:
                raise ValueError(f"L'opérateur {self.operator.value} nécessite `value`.")

        if self.value_type == ValueType.NUMERIC and self.value is not None:
            if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
                raise ValueError("Un critère NUMERIC ne peut pas recevoir une valeur non numérique.")

        if self.value_type == ValueType.DATE and self.value is not None:
            self._validate_date(self.value)

        if self.value_type == ValueType.BOOLEAN and self.value is not None:
            if not isinstance(self.value, bool):
                raise ValueError("Un critère BOOLEAN ne peut recevoir qu'une valeur booléenne.")

        return self

    @staticmethod
    def _validate_date(value) -> None:
        try:
            date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"Date invalide : {value!r} (format attendu YYYY-MM-DD).") from exc

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "RuleValueData":
        return cls.model_validate(json.loads(raw))
