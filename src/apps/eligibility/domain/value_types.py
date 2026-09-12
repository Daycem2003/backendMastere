from enum import Enum


class ValueType(str, Enum):
    NUMERIC = "NUMERIC"
    DATE = "DATE"
    DATE_RANGE = "DATE_RANGE"
    NUMERIC_RANGE = "NUMERIC_RANGE"
    STRING = "STRING"
    ENUM = "ENUM"
    BOOLEAN = "BOOLEAN"


class Operator(str, Enum):
    EQ = "="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"  # implicite pour NUMERIC_RANGE / DATE_RANGE, jamais fourni explicitement


# Opérateurs valides par type de valeur — utilisé par la validation
# (section 8 de la spec : "un opérateur numérique ne doit pas être utilisé
# avec une chaîne arbitraire").
VALID_OPERATORS_BY_TYPE: dict[ValueType, set[Operator]] = {
    ValueType.NUMERIC: {Operator.EQ, Operator.NEQ, Operator.GT, Operator.GTE, Operator.LT, Operator.LTE},
    ValueType.DATE: {Operator.EQ, Operator.NEQ, Operator.GT, Operator.GTE, Operator.LT, Operator.LTE},
    ValueType.STRING: {Operator.EQ, Operator.NEQ, Operator.IN, Operator.NOT_IN},
    ValueType.ENUM: {Operator.EQ, Operator.NEQ, Operator.IN, Operator.NOT_IN},
    ValueType.BOOLEAN: {Operator.EQ, Operator.NEQ},
    ValueType.NUMERIC_RANGE: set(),  # pas d'opérateur : min/max définissent l'intervalle
    ValueType.DATE_RANGE: set(),
}
