import json

def _table(headers, rows):
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)

def _bullets(points):
    if not points: return "- TBD"
    out = []
    for p in points:
        p = (p or "").strip()
        if "::" in p:
            head, tail = p.split("::", 1)
            out.append(f"- {head.strip()}")
            for s in [x.strip() for x in tail.split(";") if x.strip()]:
                out.append(f"  - {s}")
        else:
            out.append(f"- {p}")
    return "\n".join(out)

def onepager_md(summary: dict) -> str:
    objs = summary.get("objectives", [])
    syn = summary.get("synthesis", [])
    issues = summary.get("key_issues", [])
    concl = summary.get("conclusion_next_steps", [])
    biz = summary.get("business_perspective", "")
    verb = summary.get("verbatims", [])

    md = []
    md.append("# Compte rendu")

    md.append("\n## 1. Objectifs de la réunion")
    md.append(_bullets(objs))

    md.append("\n## 2. Synthèse des échanges")
    md.append(_bullets(syn))

    md.append("\n## 3. Principaux enjeux")
    md.append(_bullets(issues))

    md.append("\n## 4. Conclusion et prochaines étapes")
    md.append(_bullets(concl))

    md.append("\n## Mise en perspective business (interne)")
    md.append(biz or "TBD")

    if verb:
        md.append("\n## Annexes — Verbatims")
        for v in verb[:6]:
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