THRESHOLD = 0.15


def violated_pillars(continuity: float, reciprocity: float, sovereignty: float, tau: float = THRESHOLD) -> list[str]:
    violated = []
    if continuity < tau:
        violated.append("Continuity")
    if reciprocity < tau:
        violated.append("Reciprocity")
    if sovereignty < tau:
        violated.append("Sovereignty")
    return violated


def weakest_pillar(continuity: float, reciprocity: float, sovereignty: float) -> str:
    pillars = {
        "Continuity": continuity,
        "Reciprocity": reciprocity,
        "Sovereignty": sovereignty,
    }
    return min(pillars, key=pillars.get)


def correction_for_pillar(pillar: str) -> str:
    if pillar == "Continuity":
        return "enforce project alignment"
    if pillar == "Reciprocity":
        return "increase signal + feedback"
    return "fix invalid tasks + diversify decisions"


def governor_state(continuity: float, reciprocity: float, sovereignty: float, tau: float = THRESHOLD) -> dict:
    violated = violated_pillars(continuity, reciprocity, sovereignty, tau)
    active = len(violated) > 0
    corrections = [{"pillar": p, "action": correction_for_pillar(p)} for p in violated]
    return {
        "active": active,
        "violated_pillars": violated,
        "corrections": corrections,
    }


def compute_alert(continuity: float, reciprocity: float, sovereignty: float) -> tuple[str, str]:
    weakest = weakest_pillar(continuity, reciprocity, sovereignty)
    state = governor_state(continuity, reciprocity, sovereignty, THRESHOLD)

    if not state["active"]:
        return weakest, "System stable"

    if weakest == "Continuity":
        return weakest, "Continuity collapse: enforce project alignment"
    if weakest == "Reciprocity":
        return weakest, "Reciprocity collapse: increase signal + feedback"
    return weakest, "Sovereignty collapse: fix invalid tasks + diversify decisions"
