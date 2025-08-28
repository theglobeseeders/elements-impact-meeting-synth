import os, json, pathlib, traceback
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from render_onepager import onepager_md, email_md

# --- Clé API (secrets Streamlit > .env en local) ---
def get_api_key():
    try:
        return st.secrets["OPENAI_API_KEY"]  # Cloud / secrets.toml
    except Exception:
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")   # Local / .env

api_key = get_api_key()
if not api_key:
    st.error("OPENAI_API_KEY manquant (ajoute-le dans .streamlit/secrets.toml ou dans .env).")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Fichiers projet ---
BASE = pathlib.Path(__file__).parent
SCHEMA = json.loads((BASE / "schema.json").read_text(encoding="utf-8"))
PROFILE = json.loads((BASE / "cabinet_profile.json").read_text(encoding="utf-8"))
SYSTEM_PROMPT = (BASE / "prompts_system.txt").read_text(encoding="utf-8") + "\n" + json.dumps(PROFILE, ensure_ascii=False)
INSTR_PROMPT = (BASE / "prompts_extraction.txt").read_text(encoding="utf-8")

# --- UI ---
st.set_page_config(page_title="Synthèse de réunion — Elements Impact", layout="wide")
st.title("📝 Synthèse de réunion — Elements Impact")

tab1, tab2 = st.tabs(["📄 Uploader un fichier", "✍️ Coller des notes"])
transcript = None
with tab1:
    up = st.file_uploader("Fichier .txt", type=["txt"])
    if up:
        transcript = up.read().decode("utf-8", errors="ignore")
with tab2:
    txt = st.text_area("Colle tes notes brutes (sans timecodes/speakers obligatoires)", height=240)
    if txt and not transcript:
        transcript = txt

colL, colR = st.columns([3,2])
with colR:
    model = st.selectbox("Modèle", ["gpt-4o-2024-08-06", "gpt-4o-mini"], index=0)
    st.caption("ℹ️ Recommandation : température = **0.2** pour un rendu rigoureux et percutant")
    temperature = st.slider("Créativité (temperature)", 0.0, 1.0, 0.2, 0.1)
    run = st.button("🚀 Générer la synthèse", type="primary", use_container_width=True)

def _as_bullets(items):
    if not items: return "- TBD"
    return "\n".join([f"- {i}" for i in items])

if run:
    if not transcript or not transcript.strip():
        st.error("Merci de charger un fichier ou de coller des notes.")
    else:
        try:
            with st.spinner("⏳ Génération en cours…"):
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\n{INSTR_PROMPT}"}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {"name": "MeetingSummary", "schema": SCHEMA, "strict": True}
                    },
                    temperature=temperature,
                )
                summary = json.loads(completion.choices[0].message.content)

            st.success("✅ Synthèse générée")

            left, right = st.columns([3,2])
            with left:
                st.subheader("One-pager (Markdown)")
                md = onepager_md(summary)
                st.markdown(md)
            with right:
                st.subheader("Email (texte)")
                st.text(email_md(summary))

            st.divider()
            st.subheader("Aperçu structuré (extrait)")
            st.write({"objectives": summary.get("objectives", [])})
            st.write({"key_points": summary.get("key_points", [])})
            st.write({"synthesis": summary.get("synthesis", [])})
            st.write({"conclusion": summary.get("conclusion", [])})
            st.write({"next_steps": summary.get("next_steps", [])})
            st.write({"internal_analysis": summary.get("internal_analysis", {})})

            st.download_button("📥 Télécharger le JSON",
                               data=json.dumps(summary, ensure_ascii=False, indent=2),
                               file_name="summary.json", mime="application/json")
            st.download_button("📥 Télécharger le One-pager (MD)",
                               data=md, file_name="onepager.md", mime="text/markdown")

        except Exception as e:
            st.error("❌ Erreur lors de la génération.")
            st.exception(e)
            st.text(traceback.format_exc())