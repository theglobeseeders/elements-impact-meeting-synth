import os, json, argparse, pathlib
from dotenv import load_dotenv
from openai import OpenAI
from render_onepager import onepager_md, email_md

def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_text(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Agent de synthèse de réunion (style cabinet de conseil)")
    parser.add_argument("--transcript", type=str, default="sample_transcript.txt", help="Chemin du transcript brut (.txt)")
    parser.add_argument("--out", type=str, default="out", help="Dossier de sortie")
    parser.add_argument("--model", type=str, default="gpt-4o-2024-08-06", help="Modèle OpenAI")
    args = parser.parse_args()

    load_dotenv()
    client = OpenAI()

    base = pathlib.Path(__file__).parent
    transcript = load_text(str(base / args.transcript))
    schema = json.loads(load_text(str(base / "schema.json")))
    profil_cabinet = json.loads(load_text(str(base / "cabinet_profile.json")))

    # ⚠️ utilisation des fichiers sans "/"
    system = load_text(str(base / "prompts_system.txt")) + "\n" + json.dumps(profil_cabinet, ensure_ascii=False)
    instruction = load_text(str(base / "prompts_extraction.txt"))

    # Appel LLM avec Structured Outputs (JSON Schema strict)
    completion = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\n{instruction}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "MeetingSummary",
                "schema": schema,
                "strict": True
            }
        },
        temperature=0.1,
    )

    content = completion.choices[0].message.content
    try:
        summary = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        summary = json.loads(content[start:end+1])

    outdir = base / args.out
    os.makedirs(outdir, exist_ok=True)

    # Sauvegarde JSON + rendu Markdown & email
    save_text(str(outdir / "summary.json"), json.dumps(summary, ensure_ascii=False, indent=2))
    save_text(str(outdir / "onepager.md"), onepager_md(summary))
    save_text(str(outdir / "email.md"), email_md(summary))

    print(f"✅ Généré : {outdir / 'summary.json'}")
    print(f"✅ Généré : {outdir / 'onepager.md'}")
    print(f"✅ Généré : {outdir / 'email.md'}")

if __name__ == "__main__":
    main()