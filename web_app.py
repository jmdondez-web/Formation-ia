#!/usr/bin/env python3
# ============================================
# Web app "Mentor IA" — Flask
# Sert une page responsive (tél/tablette), génère les leçons via le mentor
# Claude, évalue les réponses libres, et sauvegarde la progression.
# ============================================

import json
import logging
import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

import curriculum
import mentor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")

PROGRESS_FILE = "web_progress.json"
CACHE_FILE = "lessons_cache.json"


# --------------------------------------------------
# Petits stores JSON
# --------------------------------------------------
def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _cert_progress(cert_id):
    db = _load(PROGRESS_FILE, {})
    return db.get(cert_id, {"index": 0, "completed": [], "last_ts": ""})


def _set_cert_progress(cert_id, data):
    db = _load(PROGRESS_FILE, {})
    db[cert_id] = data
    _save(PROGRESS_FILE, db)


# --------------------------------------------------
# Leçons : génération + cache (stable pour la révision espacée)
# --------------------------------------------------
def _lesson_cached(cert_id, index):
    cache = _load(CACHE_FILE, {})
    return cache.get(f"{cert_id}:{index}")


def _cache_lesson(cert_id, index, lecon):
    cache = _load(CACHE_FILE, {})
    cache[f"{cert_id}:{index}"] = lecon
    _save(CACHE_FILE, cache)


# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/certs")
def certs():
    data = []
    for cid, titre, desc, total in curriculum.list_certs():
        prog = _cert_progress(cid)
        data.append(
            {
                "id": cid,
                "titre": titre,
                "description": desc,
                "total": total,
                "index": prog["index"],
                "done": len({c["index"] for c in prog["completed"]}),
            }
        )
    return jsonify(data)


@app.route("/api/lesson")
def lesson():
    cert_id = request.args.get("cert", "")
    index = int(request.args.get("index", 0))

    info = curriculum.get_sujet(cert_id, index)
    if info is None:
        return jsonify({"done": True, "message": "Piste terminée 🎉"})

    cert, module, sujet, pos, total = info

    lecon = _lesson_cached(cert_id, index)
    if lecon is None:
        try:
            lecon = mentor.generer_lecon(cert["titre"], module["titre"], sujet, pos, total)
            _cache_lesson(cert_id, index, lecon)
        except Exception as e:
            logger.exception("Échec génération leçon")
            return jsonify({"error": f"Génération impossible : {e}"}), 502

    return jsonify(
        {
            "done": False,
            "cert": cert_id,
            "cert_titre": cert["titre"],
            "module": module["titre"],
            "sujet": sujet,
            "position": pos,
            "total": total,
            "lecon": lecon,
        }
    )


@app.route("/api/answer", methods=["POST"])
def answer():
    """QCM : vérifie la lettre, enregistre la progression, avance l'index."""
    body = request.get_json(force=True)
    cert_id = body.get("cert", "")
    index = int(body.get("index", 0))
    reponse = (body.get("reponse") or "").strip().upper()

    lecon = _lesson_cached(cert_id, index)
    if not lecon:
        return jsonify({"error": "Leçon introuvable"}), 404

    bonne = lecon["quiz"]["reponse"]
    correct = reponse == bonne

    prog = _cert_progress(cert_id)
    prog["completed"] = [c for c in prog["completed"] if c["index"] != index]
    prog["completed"].append(
        {"index": index, "ts": datetime.now().isoformat(), "correct": correct}
    )
    prog["index"] = max(prog["index"], index + 1)
    prog["last_ts"] = datetime.now().isoformat()
    _set_cert_progress(cert_id, prog)

    return jsonify(
        {
            "correct": correct,
            "bonne": bonne,
            "explication": lecon["quiz"]["explication"],
        }
    )


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """Question ouverte : le mentor évalue la réponse libre."""
    body = request.get_json(force=True)
    cert_id = body.get("cert", "")
    index = int(body.get("index", 0))
    reponse = (body.get("reponse") or "").strip()

    if not reponse:
        return jsonify({"error": "Réponse vide"}), 400

    lecon = _lesson_cached(cert_id, index)
    if not lecon:
        return jsonify({"error": "Leçon introuvable"}), 404

    info = curriculum.get_sujet(cert_id, index)
    sujet = info[2] if info else lecon["titre"]
    attendu = " ; ".join(lecon["points_cles"])

    try:
        result = mentor.evaluer_reponse(
            sujet, lecon["question_ouverte"], attendu, reponse
        )
    except Exception as e:
        logger.exception("Échec évaluation")
        return jsonify({"error": f"Évaluation impossible : {e}"}), 502

    return jsonify(result)


@app.route("/api/progress")
def progress():
    cert_id = request.args.get("cert", "")
    prog = _cert_progress(cert_id)
    total = curriculum.total_lecons(cert_id)
    done = {c["index"] for c in prog["completed"]}
    bons = sum(1 for c in prog["completed"] if c["correct"])
    return jsonify(
        {
            "total": total,
            "done": len(done),
            "correct": bons,
            "index": prog["index"],
            "last_ts": prog["last_ts"],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info("🌐 Mentor IA sur http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
