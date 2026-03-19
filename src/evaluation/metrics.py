"""Calcul des métriques d'évaluation : taux de conformité et matrice de confusion."""

from collections import defaultdict

from sklearn.metrics import classification_report, confusion_matrix

from src.config import DETERMINISTIC_WEIGHT, LLM_WEIGHT


ALL_RULES = ["R1", "R2", "R3", "R4", "R5"]


def compute_llm_score(judge_result: dict) -> float:
    """Calcule le score LLM normalisé (0-1) à partir des 5 critères."""
    criteria = [
        "ton_professionnalisme",
        "completude",
        "exactitude_donnees",
        "respect_regles_metier",
        "concision_clarte",
    ]
    total = sum(judge_result.get(c, 0) for c in criteria)
    return total / (5 * 5)  # Max = 25


def compute_conformity_rate(evaluated_results: list[dict]) -> dict:
    """Calcule le taux de conformité global et par règle.

    Returns:
        dict avec 'global', 'par_regle', et 'details'.
    """
    det_scores = []
    llm_scores = []
    rule_scores = defaultdict(list)

    for r in evaluated_results:
        det_score = r.get("deterministic", {}).get("score", 1.0)
        llm_score = compute_llm_score(r.get("llm_judge", {}))

        det_scores.append(det_score)
        llm_scores.append(llm_score)

        # Scores par règle
        rules = r.get("deterministic", {}).get("rules_detected", set())
        combined = DETERMINISTIC_WEIGHT * det_score + LLM_WEIGHT * llm_score
        for rule in rules:
            rule_scores[rule].append(combined)

    # Taux global = moyenne pondérée (40% déterministe, 60% LLM)
    if det_scores:
        avg_det = sum(det_scores) / len(det_scores)
        avg_llm = sum(llm_scores) / len(llm_scores)
        global_rate = DETERMINISTIC_WEIGHT * avg_det + LLM_WEIGHT * avg_llm
    else:
        avg_det = avg_llm = global_rate = 0.0

    # Taux par règle
    per_rule = {}
    for rule in ALL_RULES:
        scores = rule_scores.get(rule, [])
        per_rule[rule] = sum(scores) / len(scores) if scores else None

    return {
        "global": global_rate,
        "deterministic_avg": avg_det,
        "llm_avg": avg_llm,
        "par_regle": per_rule,
        "n_tours": len(evaluated_results),
    }


def compute_confusion_matrix(evaluated_results: list[dict]) -> dict:
    """Calcule la matrice de confusion par règle.

    Compare les règles détectées par le système déterministe (attendues)
    avec les règles détectées par le LLM-as-judge.

    Returns:
        dict par règle avec matrice de confusion et classification report.
    """
    results_by_rule = {}

    for rule in ALL_RULES:
        y_true = []
        y_pred = []

        for r in evaluated_results:
            expected = rule in r.get("deterministic", {}).get("rules_detected", set())
            # Règles détectées par le LLM-judge
            llm_rules = r.get("llm_judge", {}).get("regles_actives", [])
            predicted = rule in llm_rules

            y_true.append(1 if expected else 0)
            y_pred.append(1 if predicted else 0)

        if any(y_true) or any(y_pred):
            cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
            report = classification_report(
                y_true, y_pred,
                labels=[0, 1],
                target_names=[f"Non-{rule}", rule],
                output_dict=True,
                zero_division=0,
            )
            results_by_rule[rule] = {
                "confusion_matrix": cm.tolist(),
                "classification_report": report,
                "y_true": y_true,
                "y_pred": y_pred,
            }

    return results_by_rule


def format_results(conformity: dict, confusion: dict) -> str:
    """Formate les résultats pour l'affichage."""
    lines = []
    lines.append("=" * 60)
    lines.append("RÉSULTATS D'ÉVALUATION")
    lines.append("=" * 60)

    lines.append(f"\nTaux de conformité global : {conformity['global']:.1%}")
    lines.append(f"  - Déterministe ({DETERMINISTIC_WEIGHT:.0%}) : {conformity['deterministic_avg']:.1%}")
    lines.append(f"  - LLM-as-judge ({LLM_WEIGHT:.0%}) : {conformity['llm_avg']:.1%}")
    lines.append(f"  - Nombre de tours évalués : {conformity['n_tours']}")

    lines.append("\nTaux de conformité par règle :")
    for rule in ALL_RULES:
        rate = conformity["par_regle"].get(rule)
        if rate is not None:
            lines.append(f"  {rule} : {rate:.1%}")
        else:
            lines.append(f"  {rule} : N/A (aucun tour applicable)")

    lines.append("\n" + "=" * 60)
    lines.append("MATRICE DE CONFUSION PAR RÈGLE")
    lines.append("=" * 60)

    for rule in ALL_RULES:
        if rule not in confusion:
            continue
        cm = confusion[rule]["confusion_matrix"]
        report = confusion[rule]["classification_report"]

        lines.append(f"\n{rule} :")
        lines.append(f"  Matrice de confusion :")
        lines.append(f"                 Prédit Non-{rule}  Prédit {rule}")
        lines.append(f"  Réel Non-{rule}      {cm[0][0]:>4}          {cm[0][1]:>4}")
        lines.append(f"  Réel {rule}           {cm[1][0]:>4}          {cm[1][1]:>4}")

        # Precision, recall, F1 pour la classe positive
        if rule in report:
            p = report[rule].get("precision", 0)
            r = report[rule].get("recall", 0)
            f1 = report[rule].get("f1-score", 0)
            lines.append(f"  Precision: {p:.2f}  Recall: {r:.2f}  F1: {f1:.2f}")

    return "\n".join(lines)
