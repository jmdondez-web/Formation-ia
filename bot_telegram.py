#!/usr/bin/env python3
# ============================================
# Bot Telegram - Formation IA par CERTIFICATIONS
# Première certification : "Claude" (prép. examen Anthropic).
# Contenu curé en dur dans certifications.py.
# ============================================

import os
import json
import logging
from datetime import datetime

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import certifications as certs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Token depuis .env
# --------------------------------------------------
TOKEN = None
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TOKEN="):
                TOKEN = line.split("=", 1)[1].strip().strip('"')
                break
except FileNotFoundError:
    logger.error("Fichier .env introuvable. Lancez setup.sh d'abord.")
    raise SystemExit(1)

if not TOKEN:
    logger.error("TOKEN absent du fichier .env.")
    raise SystemExit(1)

# Certification par défaut (première de la liste).
DEFAULT_CERT = "claude"

# --------------------------------------------------
# Persistance (fichier JSON)
# --------------------------------------------------
DB_FILE = "progression.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def _default_user():
    return {
        "cert": None,        # certification en cours
        "lecon": 0,          # index global de leçon
        "score": 0,          # bonnes réponses cumulées (leçons)
        "date": "",          # dernière activité
        "mode": "lecon",     # "lecon" ou "examen"
        "exam_idx": 0,       # question d'examen en cours
        "exam_ok": 0,        # bonnes réponses à l'examen en cours
        "certifie": False,   # a réussi l'examen final ?
        "meilleur": 0.0,     # meilleur score d'examen (ratio)
    }


def get_user(user_id):
    db = load_db()
    user = db.get(str(user_id))
    if user is None:
        user = _default_user()
    else:
        # Migration douce des anciens enregistrements.
        for k, v in _default_user().items():
            user.setdefault(k, v)
    return user


def save_user(user_id, data):
    db = load_db()
    db[str(user_id)] = data
    save_db(db)


# --------------------------------------------------
# Envoi Markdown robuste (fallback texte brut)
# --------------------------------------------------
async def send_md(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except BadRequest:
        # Markdown mal formé : on renvoie en texte brut pour ne jamais perdre un message.
        await update.message.reply_text(text)


# --------------------------------------------------
# Commandes
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    cert_en_cours = user["cert"] or "—"
    await send_md(
        update,
        f"👋 Bonjour {update.effective_user.first_name} !\n\n"
        "Bienvenue dans ta formation IA *par certifications*.\n\n"
        f"📊 Certification en cours : *{cert_en_cours}* | "
        f"Leçon {user['lecon']} | Score {user['score']}\n\n"
        "Commandes :\n"
        "/certifications – Voir les certifications disponibles\n"
        "/commencer – Démarrer (ou reprendre) une certification\n"
        "/lecon – Recevoir la prochaine leçon\n"
        "/quiz <réponse> – Répondre au quiz / à l'examen (ex : /quiz B)\n"
        "/examen – Passer l'examen final de la certification\n"
        "/progression – Voir ton avancement\n"
        "/reset – Recommencer la certification",
    )


async def certifications_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lignes = ["🎓 *Certifications disponibles*\n"]
    for cid, titre, desc in certs.list_certifications():
        lignes.append(f"• *{cid}* — {titre}\n  {desc}")
    lignes.append("\nTape /commencer pour démarrer la première (*claude*).")
    await send_md(update, "\n".join(lignes))


async def commencer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    # Choix de certification : argument optionnel, sinon défaut.
    cert_id = (context.args[0].lower() if context.args else DEFAULT_CERT)
    cert = certs.get_certification(cert_id)
    if cert is None:
        await send_md(update, f"❓ Certification inconnue : `{cert_id}`. Tape /certifications.")
        return

    # Si on change de certification, on repart de zéro pour celle-ci.
    if user["cert"] != cert_id:
        user.update(_default_user())
        user["cert"] = cert_id
        save_user(user_id, user)

    await send_md(
        update,
        f"🚀 Certification *{cert_id}* démarrée !\n\n"
        f"{cert['titre']}\n{cert['officiel']}\n\n"
        f"📚 {len(cert['modules'])} modules · {certs.total_lecons(cert_id)} leçons, "
        "puis un examen final.\n\nTape /lecon pour commencer.",
    )


def _ensure_cert(user, user_id):
    """Sélectionne la certification par défaut si aucune n'est en cours."""
    if not user["cert"]:
        user["cert"] = DEFAULT_CERT
        save_user(user_id, user)
    return user["cert"]


async def lecon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    cert_id = _ensure_cert(user, user_id)

    if user["mode"] == "examen":
        await send_md(update, "📝 Tu es en plein examen. Réponds avec /quiz, ou /reset pour annuler.")
        return

    info = certs.get_lecon(cert_id, user["lecon"])
    if info is None:
        total = certs.total_lecons(cert_id)
        await send_md(
            update,
            f"🎉 Toutes les leçons ({total}) sont terminées pour *{cert_id}* !\n\n"
            "Tape /examen pour passer l'examen final de certification.",
        )
        return

    module, data, pos, total = info
    await send_md(
        update,
        f"📚 *Leçon {pos + 1}/{total}* — {module['titre']}\n\n{data['contenu']}",
    )
    quiz = data["quiz"]
    await send_md(
        update,
        f"❓ *Quiz :* {quiz['question']}\n\n"
        + "\n".join(quiz["choix"])
        + "\n\nRéponds avec /quiz suivi de ta réponse (ex : /quiz B)",
    )


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    cert_id = _ensure_cert(user, user_id)

    reponse = " ".join(context.args).strip().upper()
    if not reponse:
        await send_md(update, "Indique ta réponse, ex : /quiz B")
        return

    if user["mode"] == "examen":
        await _quiz_examen(update, user_id, user, cert_id, reponse)
    else:
        await _quiz_lecon(update, user_id, user, cert_id, reponse)


async def _quiz_lecon(update, user_id, user, cert_id, reponse):
    info = certs.get_lecon(cert_id, user["lecon"])
    if info is None:
        await send_md(update, "Pas de quiz en attente. Tape /lecon ou /examen.")
        return

    _, data, _, total = info
    bonne = data["quiz"]["reponse"]
    user["date"] = datetime.now().isoformat()

    if reponse == bonne:
        user["score"] += 1
        user["lecon"] += 1
        save_user(user_id, user)
        reste = total - user["lecon"]
        suite = "Tape /examen pour l'examen final 🎯" if reste <= 0 else "Tape /lecon pour la suite."
        await send_md(update, f"✅ *Bonne réponse !* Score : {user['score']}\n\n{suite}")
    else:
        user["lecon"] += 1
        save_user(user_id, user)
        await send_md(
            update,
            f"❌ Pas tout à fait — la bonne réponse était *{bonne}*.\n"
            "Retiens-la et tape /lecon pour continuer.",
        )


async def examen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    cert_id = _ensure_cert(user, user_id)

    total = certs.total_lecons(cert_id)
    if user["lecon"] < total:
        await send_md(
            update,
            f"⏳ Termine d'abord les leçons ({user['lecon']}/{total}) avant l'examen. Tape /lecon.",
        )
        return

    exam = certs.get_examen(cert_id)
    if not exam or not exam["questions"]:
        await send_md(update, "Aucun examen défini pour cette certification.")
        return

    user["mode"] = "examen"
    user["exam_idx"] = 0
    user["exam_ok"] = 0
    save_user(user_id, user)

    n = len(exam["questions"])
    seuil = int(exam["seuil"] * 100)
    await send_md(
        update,
        f"📝 *Examen final — {cert_id}*\n\n"
        f"{n} questions · seuil de réussite : {seuil} %.\n"
        "Réponds à chaque question avec /quiz <lettre>.\n",
    )
    await _envoyer_question_examen(update, exam, 0)


async def _envoyer_question_examen(update, exam, idx):
    q = exam["questions"][idx]
    n = len(exam["questions"])
    await send_md(
        update,
        f"❓ *Question {idx + 1}/{n}*\n{q['question']}\n\n" + "\n".join(q["choix"]),
    )


async def _quiz_examen(update, user_id, user, cert_id, reponse):
    exam = certs.get_examen(cert_id)
    idx = user["exam_idx"]
    questions = exam["questions"]

    if reponse == questions[idx]["reponse"]:
        user["exam_ok"] += 1

    idx += 1
    user["exam_idx"] = idx

    if idx < len(questions):
        save_user(user_id, user)
        await _envoyer_question_examen(update, exam, idx)
        return

    # Fin de l'examen → calcul du résultat.
    n = len(questions)
    ratio = user["exam_ok"] / n
    user["mode"] = "lecon"
    user["meilleur"] = max(user.get("meilleur", 0.0), ratio)
    user["date"] = datetime.now().isoformat()
    reussi = ratio >= exam["seuil"]
    if reussi:
        user["certifie"] = True
    save_user(user_id, user)

    pct = round(ratio * 100)
    seuil = round(exam["seuil"] * 100)
    if reussi:
        await send_md(
            update,
            f"🏆 *Réussi !* {user['exam_ok']}/{n} ({pct} %, seuil {seuil} %).\n\n"
            f"Tu es *prêt* à passer la certification officielle *{cert_id}* d'Anthropic. "
            "Bravo ! 🎉",
        )
    else:
        await send_md(
            update,
            f"📊 {user['exam_ok']}/{n} ({pct} %) — il faut {seuil} %.\n\n"
            "Pas encore prêt : revois les leçons (/reset puis /lecon) et retente /examen.",
        )


async def progression(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    cert_id = user["cert"] or DEFAULT_CERT
    total = certs.total_lecons(cert_id)
    badge = "✅ prêt pour l'examen officiel" if user.get("certifie") else "en cours"
    meilleur = round(user.get("meilleur", 0.0) * 100)
    await send_md(
        update,
        "📊 *Progression*\n\n"
        f"Certification : *{cert_id}* ({badge})\n"
        f"Leçons : {min(user['lecon'], total)}/{total}\n"
        f"Score leçons : {user['score']}\n"
        f"Meilleur score d'examen : {meilleur} %\n"
        f"Dernière activité : {user['date'][:10] if user['date'] else 'Jamais'}",
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    cert_id = user["cert"] or DEFAULT_CERT
    fresh = _default_user()
    fresh["cert"] = cert_id
    save_user(update.effective_user.id, fresh)
    await send_md(update, f"🔄 Progression réinitialisée pour *{cert_id}*. Tape /lecon pour recommencer.")


async def reponse_texte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_md(
        update,
        "Utilise les commandes :\n"
        "/lecon – Leçon suivante\n"
        "/quiz <réponse> – Répondre\n"
        "/examen – Examen final\n"
        "/progression – Avancement",
    )


# --------------------------------------------------
# Lancement
# --------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("certifications", certifications_cmd))
    app.add_handler(CommandHandler("commencer", commencer))
    app.add_handler(CommandHandler("lecon", lecon))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("examen", examen))
    app.add_handler(CommandHandler("progression", progression))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reponse_texte))

    logger.info("🤖 Bot certifications démarré !")
    app.run_polling()


if __name__ == "__main__":
    main()
