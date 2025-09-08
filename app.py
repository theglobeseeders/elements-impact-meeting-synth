import os, json, pathlib, traceback
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from render_onepager import onepager_md, email_md

# =========================
#  Helpers: API key loading
# =========================
def get_api_key() -> str | None:
    """
    Try Streamlit Secrets first (Cloud), then local .env.
    """
    try:
        return st.secrets["OPENAI_API_KEY"]  # Cloud / .streamlit/secrets.toml
    except Exception:
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")   # Local / .env

api_key = get_api_key()
if not api_key:
    st.error("OPENAI_API_KEY manquant (ajoute-le dans .streamlit/secrets.toml ou dans .env).")
    st.stop()

client = OpenAI(api_key=api_key)

# =========================
#  Files & prompts loading
# =========================
BASE = pathlib.Path(__file__).parent

# Schema V2 (Objectifs / Synthèse / Enjeux / Conclusion & Étapes / Business perspective / Verbatims)
SCHEMA_PATH = BASE / "schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

# Corpus business (cabinet_profile + extraits plaquette + cas clients, etc.)
CORPUS_PATH = BASE / "business_corpus.txt"
CORPUS = CORPUS_PATH.read_text(encoding="utf-8") if CORPUS_PATH.exists() else ""

SYSTEM_PROMPT = (
    (BASE / "prompts_system.txt").read_text(encoding="utf-8")
    + "\n\n[Corpus interne Elements]\n"
    + CORPUS
)
INSTR_PROMPT = (BASE / "prompts_extraction.txt").read_text(encoding="utf-8")

# ===============
#  Streamlit App
# ===============
st.set_page_config(page_title="Synthèse de réunion — Elements Impact", layout="wide")
st.title("📝 Synthèse de réunion — Elements Impact")

st.caption(
    "Charge un fichier texte, un audio, ou colle tes notes. "
    "La sortie suit la trame : **Objectifs / Synthèse / Enjeux / Conclusion & étapes / Mise en perspective business**. "
    "Les échanges personnels sont filtrés, et la perspective business est nourrie par ton corpus interne."
)

# ---- Inputs
tab_txt, tab_audio, tab_paste = st.tabs(["📄 Fichier .txt", "🎙️ Audio (.mp3/.wav/.m4a)", "✍️ Coller des notes"])
transcript: str | None = None

with tab_txt:
    up_txt = st.file_uploader("Uploader un .txt", type=["txt"], key="txtuploader")
    if up_txt:
        transcript = up_txt.read().decode("utf-8", errors="ignore")

with tab_audio:
    up_audio = st.file_uploader("Uploader un fichier audio", type=["mp3", "wav", "m4a"], key="audiouploader")
    if up_audio and not transcript:
        with st.spinner("⏳ Transcription audio en cours…"):
            try:
                # OpenAI Audio Transcribe (gpt-4o-mini-transcribe)
                tr = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=up_audio
                )
                transcript = tr.text
                st.success("✅ Transcription terminée.")
            except Exception as e:
                st.error("❌ Erreur pendant la transcription audio.")
                st.exception(e)

with tab_paste:
    pasted = st.text_area("Colle tes notes brutes ici (sans timecodes/speakers obligatoires)", height=220)
    if pasted and not transcript:
        transcript = pasted

# ---- Controls
colL, colR = st.columns([3, 2], gap="large")
with colR:
    model = st.selectbox("Modèle", ["gpt-4o-2024-08-06", "gpt-4o-mini"], index=0)
    st.caption("ℹ️ Recommandation : température = **0.2** pour un rendu rigoureux et percutant")
    temperature = st.slider("Créativité (temperature)", 0.0, 1.0, value=0.2, step=0.1)
    run = st.button("🚀 Générer la synthèse", type="primary", use_container_width=True)

# =============
#  Generation
# =============
def generate_summary(text: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"TRANSCRIPT:\n{text}\n\n{INSTR_PROMPT}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "MeetingSummary", "schema": SCHEMA, "strict": True}
        },
        temperature=temperature,
    )
    return json.loads(completion.choices[0].message.content)

if run:
    if not transcript or not transcript.strip():
        st.error("Merci de charger un .txt, un audio, ou de coller des notes.")
    else:
        try:
            with st.spinner("⏳ Génération en cours…"):
                summary = generate_summary(transcript)

            # ---- Garde-fou : présence de business perspective non générique
            bp = (summary.get("business_perspective") or "").lower()
            hint_words = ["strategy", "stratégie", "operations", "opérations", "digital", "impact", "boussole"]
            if not any(w in bp for w in hint_words):
                st.warning(
                    "⚠️ La **mise en perspective business** semble générique. "
                    "Pense à enrichir `business_corpus.txt` (offres, cas, différenciateurs) pour muscler cette section."
                )

            st.success("✅ Synthèse générée")

            # ---- Render
            left, right = st.columns([3, 2], gap="large")
            with left:
                st.subheader("One-pager (Markdown)")
                md = onepager_md(summary)
                st.markdown(md)

            with right:
                st.subheader("Email (texte)")
                st.text(email_md(summary))

                with st.expander("Aperçu structuré (brut JSON)"):
                    st.json(summary)

            # ---- Downloads
            st.download_button(
                "📥 Télécharger le JSON",
                data=json.dumps(summary, ensure_ascii=False, indent=2),
                file_name="summary.json",
                mime="application/json",
                use_container_width=True,
            )
            st.download_button(
                "📥 Télécharger le One-pager (MD)",
                data=md,
                file_name="onepager.md",
                mime="text/markdown",
                use_container_width=True,
            )

        except Exception as e:
            st.error("❌ Erreur lors de la génération.")
            st.exception(e)
            st.text(traceback.format_exc())
