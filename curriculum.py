#!/usr/bin/env python3
# ============================================
# Curriculums des certifications (web app mentor)
# Chaque piste = liste de modules, chaque module = liste de sujets.
# Les leçons sont générées dynamiquement par le mentor (mentor.py).
# ============================================

CURRICULA = {
    "claude": {
        "titre": "🟣 Certification Claude (Anthropic)",
        "description": "Maîtriser Claude : modèles, API Messages, prompting, "
        "tool use, agents/MCP.",
        "modules": [
            {
                "titre": "Les modèles Claude",
                "sujets": [
                    "La famille de modèles Claude (Opus, Sonnet, Haiku) et leurs compromis intelligence/vitesse/coût",
                    "Choisir le bon modèle selon le besoin plutôt que le prix",
                    "La fenêtre de contexte et les tokens : ce que le modèle peut traiter",
                ],
            },
            {
                "titre": "L'API Messages",
                "sujets": [
                    "Structure d'un appel : model, max_tokens, messages, system",
                    "Le rôle system vs user vs assistant et l'alternance des tours",
                    "Lire une réponse : content, stop_reason, usage (tokens)",
                    "Le streaming : afficher la réponse au fil de l'eau",
                ],
            },
            {
                "titre": "Prompting efficace",
                "sujets": [
                    "Donner des instructions claires, du contexte et des exemples (few-shot)",
                    "Forcer une sortie structurée (JSON) avec output_config.format",
                    "Le prompt caching : réutiliser un préfixe stable pour réduire coût et latence",
                ],
            },
            {
                "titre": "Tool use & agents",
                "sujets": [
                    "Le tool use : définir des outils et laisser Claude les appeler",
                    "La boucle agentique : appeler, exécuter, renvoyer le tool_result",
                    "La pensée étendue (adaptive thinking) et le paramètre effort",
                    "MCP : connecter Claude à des serveurs d'outils standardisés",
                ],
            },
        ],
    },
    "linux": {
        "titre": "🐧 Linux (fondamentaux, orienté LPIC-1 / LFCS)",
        "description": "Ligne de commande, système de fichiers, permissions, "
        "processus, paquets, réseau, systemd.",
        "modules": [
            {
                "titre": "Ligne de commande & système de fichiers",
                "sujets": [
                    "Naviguer : pwd, cd, ls, et l'arborescence Linux (/, /home, /etc, /var)",
                    "Manipuler fichiers et dossiers : cp, mv, rm, mkdir, touch",
                    "Lire et rechercher : cat, less, head, tail, grep",
                    "Les chemins absolus vs relatifs et les jokers (*, ?, [])",
                ],
            },
            {
                "titre": "Permissions & utilisateurs",
                "sujets": [
                    "Le modèle de permissions rwx : utilisateur, groupe, autres",
                    "Modifier les droits : chmod (octal et symbolique) et chown",
                    "Utilisateurs et groupes : /etc/passwd, sudo, su",
                ],
            },
            {
                "titre": "Processus & shell",
                "sujets": [
                    "Voir les processus : ps, top, et les identifiants PID",
                    "Contrôler les processus : kill, signaux, jobs, & (arrière-plan)",
                    "Redirections et pipes : >, >>, <, | pour chaîner les commandes",
                    "Variables d'environnement et le PATH",
                ],
            },
            {
                "titre": "Paquets, réseau & services",
                "sujets": [
                    "Gérer les paquets : apt (Debian/Ubuntu) — install, update, remove",
                    "Diagnostiquer le réseau : ip, ping, ss, curl",
                    "Gérer les services avec systemd : systemctl start/stop/status/enable",
                    "Consulter les logs : journalctl et /var/log",
                ],
            },
        ],
    },
}


def list_certs():
    """[(cert_id, titre, description, total_lecons), ...]"""
    return [
        (cid, c["titre"], c["description"], total_lecons(cid))
        for cid, c in CURRICULA.items()
    ]


def get_cert(cert_id):
    return CURRICULA.get(cert_id)


def total_lecons(cert_id):
    cert = CURRICULA.get(cert_id)
    if not cert:
        return 0
    return sum(len(m["sujets"]) for m in cert["modules"])


def get_sujet(cert_id, index):
    """Retourne (cert, module, sujet, position, total) ou None si hors borne."""
    cert = CURRICULA.get(cert_id)
    if not cert:
        return None
    pos = 0
    for module in cert["modules"]:
        for sujet in module["sujets"]:
            if pos == index:
                return cert, module, sujet, pos, total_lecons(cert_id)
            pos += 1
    return None
