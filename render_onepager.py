import json

def _table(headers, rows):
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)

def _bullets(points):
    """
    Rend des bullets hiérarchiques si un point contient '::' :
    - 'Thème :: sous-point A; sous-point B' devient :
      - Thème
        - sous-point A
        - sous-point B
    Sinon, rend juste un bullet par entrée.
    """
    if not points:
        return "- TBD"
    out = []
    for p in points:
        p = (p or "").strip()
        if "::" in p:
            head, tail = p.split("::", 1)
            head = head.strip()
            subs = [s.strip() for s in tail.split(";") if s.strip()]
            out.append(f"- {head}")
            for s in subs:
                out.append(f"  - {s}")
        else:
            out.append(f"- {p}")
    return "\n".join(out)

def onepager_md(summary: dict) -> str:
    objs = summary.get("objectives", [])
    kps = summary.get("key_points", [])
    syn = summary.get("synthesis", [])
    concl = summary.get("conclusion", [])
    steps = summary.get("next_steps", [])
    internal = summary.get("internal_analysis", {})
    verbatims = summary.get("verbatims", [])

    md = []
    md.append("# Compte rendu — McKinsey-like")

    md.append("\n## 1. Objectifs de la réunion")
    md.append(_bullets(objs))

    md.append("\n## 2. Principaux points abordés")
    md.append(_bullets(kps))

    md.append("\n## 3. Synthèse des échanges")
    md.append(_bullets(syn))

    md.append("\n## 4. Conclusion et mise en perspective")
    md.append(_bullets(concl))

    md.append("\n## 5. Prochaines étapes")
    if steps:
        rows = []
        for s in steps:
            rows.append([
                s.get("action", "TBD"),
                s.get("owner", "TBD"),
                s.get("deadline", "TBD"),
                s.get("status", "TBD"),
            ])
        md.append(_table(["Action", "Responsable", "Deadline", "Statut"], rows))
    else:
        md.append("_Aucune action identifiée._")

    md.append("\n## 6. Interne (confidentiel) — Intérêt stratégique pour Elements")
    md.append("**Intérêt stratégique global**")
    md.append(internal.get("strategic_interest", "TBD"))
    md.append("\n**Accelerate**")
    md.append(internal.get("accelerate", "TBD"))
    md.append("\n**Impact**")
    md.append(internal.get("impact", "TBD"))

    if verbatims:
        md.append("\n## Annexes — Verbatims sélectionnés")
        for v in verbatims[:6]:
            md.append(f"> **{v.get('speaker','Note')}** : “{v.get('quote','')}”")

    return "\n".join(md)

def email_md(summary: dict) -> str:
    """Email très concis basé sur la même structure que le onepager."""
    objs = summary.get("objectives", [])
    kps = summary.get("key_points", [])
    syn = summary.get("synthesis", [])
    concl = summary.get("conclusion", [])
    steps = summary.get("next_steps", [])

    lines = []
    lines.append("Objet : Compte rendu de réunion — Synthèse exécutive")
    lines.append("")

    if objs:
        lines.append("Objectifs : " + "; ".join(objs[:3]))

    if syn:
        # on prend les 2 premiers bullet points de synthèse
        lines.append("Synthèse : " + " / ".join(syn[:2]))

    if kps:
        lines.append("")
        lines.append("Points saillants :")
        for p in kps[:3]:
            lines.append(f"• {p}")

    if concl:
        lines.append("")
        lines.append("Conclusion : " + " / ".join(concl[:2]))

    if steps:
        lines.append("")
        lines.append("Actions :")
        for s in steps[:3]:
            lines.append(f"• {s.get('action','')} — {s.get('owner','TBD')} (délai {s.get('deadline','TBD')})")

    return "\n".join(lines)