#!/usr/bin/env python3
# ============================================
# Web app "Mentor IA" — Flask
# Sert une page responsive (tél/tablette), génère les leçons via le mentor
# Claude, évalue les réponses libres, et sauvegarde la progression.
# ============================================

import json
import logging
import os
import threading
from datetime import datetime

from flask import Flask, jsonify, request

import curriculum
import mentor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")

PROGRESS_FILE = "web_progress.json"
CACHE_FILE = "lessons_cache.json"

# Clé d'accès API (optionnelle) : si MENTOR_API_KEY est définie dans .env,
# toutes les routes /api/* exigent l'en-tête X-Mentor-Key (ou ?key=).
# La page est servie avec la clé injectée, donc la SPA fonctionne sans action
# de l'utilisateur ; mais un client externe sans clé est rejeté (401).
MENTOR_API_KEY = os.environ.get("MENTOR_API_KEY", "").strip()

# Verrou global : Flask est multi-threadé, les fichiers JSON ne supportent pas
# les accès concurrents (lecture-modification-écriture).
_JSON_LOCK = threading.RLock()


# --------------------------------------------------
# Petits stores JSON
# --------------------------------------------------
def _load(path, default):
    if not os.path.exists(path):
        return default
    with _JSON_LOCK:
        with open(path, "r") as f:
            return json.load(f)


def _save(path, data):
    # Écriture atomique : jamais de fichier à moitié écrit en cas de crash.
    tmp = f"{path}.tmp"
    with _JSON_LOCK:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def _cert_progress(cert_id):
    db = _load(PROGRESS_FILE, {})
    return db.get(cert_id, {"index": 0, "completed": [], "a_revoir": [], "last_ts": ""})


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
@app.before_request
def _check_key():
    if not MENTOR_API_KEY or not request.path.startswith("/api/"):
        return None
    key = request.headers.get("X-Mentor-Key", "") or request.args.get("key", "")
    if key != MENTOR_API_KEY:
        return jsonify({"error": "Clé d'accès invalide ou absente"}), 401
    return None


@app.route("/")
def index():
    # La clé (si définie) est injectée dans la page pour que la SPA puisse
    # appeler l'API ; elle n'est jamais committée dans le repo.
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    return html.replace("__MENTOR_KEY__", MENTOR_API_KEY)


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
                "arevoir": len(prog.get("a_revoir", [])),
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

    a_revoir = prog.setdefault("a_revoir", [])
    if correct:
        if index in a_revoir:
            a_revoir.remove(index)
    elif index not in a_revoir:
        a_revoir.append(index)
    prog["a_revoir"] = a_revoir
    _set_cert_progress(cert_id, prog)

    return jsonify(
        {
            "correct": correct,
            "bonne": bonne,
            "explication": lecon["quiz"]["explication"],
            "arevoir": len(a_revoir),
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

    prog = _cert_progress(cert_id)
    a_revoir = prog.setdefault("a_revoir", [])
    if result.get("correct"):
        if index in a_revoir:
            a_revoir.remove(index)
    elif index not in a_revoir:
        a_revoir.append(index)
    prog["a_revoir"] = a_revoir
    _set_cert_progress(cert_id, prog)
    result["arevoir"] = len(a_revoir)

    return jsonify(result)


@app.route("/api/review")
def review():
    """Leçons ratées (file « à revoir »), dans l'ordre des échecs."""
    cert_id = request.args.get("cert", "")
    prog = _cert_progress(cert_id)
    return jsonify({"cert": cert_id, "indexes": prog.get("a_revoir", [])})


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
