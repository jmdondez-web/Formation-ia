#!/usr/bin/env python3
# ============================================
# Certifications IA — contenu curé en dur
# Première certification : "Claude" (prép. examen Anthropic officiel)
#
# Structure :
#   CERTIFICATIONS[cert_id] = {
#       titre, description, officiel,
#       modules: [ {titre, lecons: [ {titre, contenu, quiz} ]} ],
#       examen: { seuil, questions: [ {question, choix, reponse} ] }
#   }
# Le bot ENTRAÎNE à la certification ; il ne délivre pas le diplôme officiel.
# ============================================


def _q(question, choix, reponse):
    return {"question": question, "choix": choix, "reponse": reponse}


CERTIFICATIONS = {
    "claude": {
        "titre": "🟣 Certification Claude (Anthropic)",
        "description": "Maîtriser Claude : modèles, API Messages, prompting, tool use, caching, agents/MCP.",
        "officiel": (
            "Cette piste prépare à la certification *Claude* d'Anthropic "
            "(Anthropic Academy). Le bot t'entraîne sur le programme officiel ; "
            "l'examen final ici valide que tu es *prêt* à passer la vraie certification — "
            "le diplôme officiel se passe côté Anthropic."
        ),
        "modules": [
            {
                "titre": "Module 1 — Claude & les modèles",
                "lecons": [
                    {
                        "titre": "La famille de modèles Claude",
                        "contenu": (
                            "🧠 *Module 1 · Leçon 1 — La famille Claude*\n\n"
                            "Claude est une famille de modèles d'Anthropic, déclinée par "
                            "compromis intelligence / vitesse / coût :\n\n"
                            "• *Opus* — le plus capable pour le raisonnement et l'agentique "
                            "(`claude-opus-4-8`).\n"
                            "• *Sonnet* — meilleur équilibre vitesse/intelligence "
                            "(`claude-sonnet-4-6`).\n"
                            "• *Haiku* — le plus rapide et économique (`claude-haiku-4-5`).\n"
                            "• *Fable* — le modèle le plus capable pour les tâches les plus "
                            "exigeantes (`claude-fable-5`).\n\n"
                            "🎯 *À retenir :* on cite un modèle par son *id exact* (ex. "
                            "`claude-opus-4-8`), sans suffixe de date inventé."
                        ),
                        "quiz": _q(
                            "Quel modèle privilégier pour la tâche la plus exigeante en raisonnement ?",
                            ["A) claude-haiku-4-5", "B) claude-fable-5", "C) claude-sonnet-4-6", "D) peu importe"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Choisir le bon modèle",
                        "contenu": (
                            "🧠 *Module 1 · Leçon 2 — Choisir le bon modèle*\n\n"
                            "Le bon réflexe : partir du *besoin*, pas du prix.\n\n"
                            "• Classification, extraction, résumé simple → *Haiku* (rapide, pas cher).\n"
                            "• Usage généraliste à fort volume → *Sonnet*.\n"
                            "• Raisonnement difficile, code, agents → *Opus* / *Fable*.\n\n"
                            "💡 On ne *rétrograde pas* un modèle juste pour économiser sans "
                            "raison : c'est un choix produit. Par défaut sur une nouvelle app, "
                            "on vise le modèle le plus capable adapté au cas d'usage."
                        ),
                        "quiz": _q(
                            "Pour de la classification de tickets en très grand volume, on choisit plutôt :",
                            ["A) Opus", "B) Fable", "C) Haiku", "D) un modèle retiré"],
                            "C",
                        ),
                    },
                    {
                        "titre": "Tokens & fenêtre de contexte",
                        "contenu": (
                            "🧠 *Module 1 · Leçon 3 — Tokens & contexte*\n\n"
                            "Un *token* ≈ un morceau de mot. Le modèle facture et raisonne en tokens.\n\n"
                            "• La *fenêtre de contexte* est la quantité max de tokens "
                            "(entrée + sortie) que le modèle peut traiter (jusqu'à 1M sur les modèles récents).\n"
                            "• `max_tokens` borne la *sortie* générée.\n"
                            "• Pour compter, on utilise l'endpoint `count_tokens` du SDK Anthropic, "
                            "*jamais* `tiktoken` (c'est le tokenizer d'un autre fournisseur).\n\n"
                            "⚠️ Si la réponse est tronquée, c'est souvent `max_tokens` trop bas."
                        ),
                        "quiz": _q(
                            "Comment compter correctement les tokens pour Claude ?",
                            ["A) avec tiktoken", "B) à la louche × 4", "C) l'endpoint count_tokens du SDK", "D) impossible"],
                            "C",
                        ),
                    },
                ],
            },
            {
                "titre": "Module 2 — L'API Messages",
                "lecons": [
                    {
                        "titre": "Structure d'une requête",
                        "contenu": (
                            "📨 *Module 2 · Leçon 1 — L'API Messages*\n\n"
                            "Tout passe par un seul endpoint : `POST /v1/messages`.\n\n"
                            "Champs essentiels :\n"
                            "• `model` — l'id du modèle.\n"
                            "• `max_tokens` — limite de tokens en sortie.\n"
                            "• `messages` — la conversation (liste de tours).\n"
                            "• `system` — les instructions de haut niveau (le rôle/comportement).\n\n"
                            "```\n"
                            "client.messages.create(\n"
                            "    model=\"claude-opus-4-8\",\n"
                            "    max_tokens=1024,\n"
                            "    system=\"Tu es un assistant concis.\",\n"
                            "    messages=[{\"role\": \"user\", \"content\": \"Bonjour\"}],\n"
                            ")\n"
                            "```"
                        ),
                        "quiz": _q(
                            "Où placer les instructions de comportement de l'assistant ?",
                            ["A) dans max_tokens", "B) dans le champ system", "C) dans le model", "D) nulle part"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Rôles & conversation multi-tours",
                        "contenu": (
                            "📨 *Module 2 · Leçon 2 — Rôles & multi-tours*\n\n"
                            "Les messages alternent les rôles `user` et `assistant`.\n\n"
                            "• Le *premier* message doit être `user`.\n"
                            "• L'API est *sans état* (stateless) : on renvoie *tout* l'historique "
                            "à chaque appel — le modèle ne « se souvient » pas tout seul.\n"
                            "• On peut aussi, sur les modèles récents, insérer un message "
                            "`system` en cours de conversation pour une instruction opérateur.\n\n"
                            "🎯 « Sans état » = ta mémoire conversationnelle, c'est *toi* qui la gères."
                        ),
                        "quiz": _q(
                            "Pourquoi renvoie-t-on tout l'historique à chaque requête ?",
                            ["A) pour payer plus", "B) car l'API est stateless", "C) c'est optionnel", "D) à cause du cache"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Streaming & stop_reason",
                        "contenu": (
                            "📨 *Module 2 · Leçon 3 — Streaming & arrêt*\n\n"
                            "Le *streaming* renvoie la réponse au fil de l'eau (meilleure latence "
                            "perçue, évite les timeouts sur longues sorties) via `messages.stream(...)`.\n\n"
                            "Le champ `stop_reason` explique pourquoi le modèle s'est arrêté :\n"
                            "• `end_turn` — fini naturellement.\n"
                            "• `max_tokens` — limite de sortie atteinte.\n"
                            "• `tool_use` — il veut appeler un outil.\n"
                            "• `refusal` — refus pour raison de sécurité.\n\n"
                            "⚠️ Toujours vérifier `stop_reason` *avant* de lire le contenu."
                        ),
                        "quiz": _q(
                            "Un `stop_reason` à `tool_use` signifie que :",
                            ["A) la réponse est finie", "B) le modèle veut appeler un outil", "C) erreur réseau", "D) limite de tokens"],
                            "B",
                        ),
                    },
                ],
            },
            {
                "titre": "Module 3 — Prompt engineering",
                "lecons": [
                    {
                        "titre": "System prompt & instructions claires",
                        "contenu": (
                            "✍️ *Module 3 · Leçon 1 — Prompting de base*\n\n"
                            "Un bon prompt est *explicite* et *contextualisé* :\n\n"
                            "• Donne le rôle et l'objectif dans le `system`.\n"
                            "• Précise le format de sortie attendu.\n"
                            "• Donne le *pourquoi* (l'intention), pas seulement la tâche.\n\n"
                            "💡 Sur les modèles récents, inutile d'en faire trop : des "
                            "instructions trop agressives (« TU DOIS ABSOLUMENT… ») font "
                            "*sur-réagir* le modèle. Sois direct et précis, pas péremptoire."
                        ),
                        "quiz": _q(
                            "Que faire des instructions du type « CRITIQUE : TU DOIS TOUJOURS… » sur un modèle récent ?",
                            ["A) en mettre partout", "B) les adoucir, elles font sur-réagir", "C) les écrire en majuscules", "D) les répéter 3 fois"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Techniques : exemples & structure",
                        "contenu": (
                            "✍️ *Module 3 · Leçon 2 — Techniques*\n\n"
                            "Leviers qui marchent :\n\n"
                            "• *Few-shot* : montrer 1 à 3 exemples du résultat voulu.\n"
                            "• *Structure* : baliser le prompt (sections, balises `<exemple>...`).\n"
                            "• *Sorties structurées* : contraindre le format via "
                            "`output_config.format` (schéma JSON) plutôt que de « préremplir » "
                            "la réponse de l'assistant (le préremplissage est *refusé* sur les "
                            "modèles récents).\n\n"
                            "🎯 Pour forcer du JSON valide : sorties structurées, pas un prefill."
                        ),
                        "quiz": _q(
                            "Pour garantir une sortie JSON valide sur un modèle récent :",
                            ["A) préremplir la réponse assistant", "B) output_config.format (schéma JSON)", "C) baisser max_tokens", "D) température 0"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Adaptive thinking & effort",
                        "contenu": (
                            "✍️ *Module 3 · Leçon 3 — Réflexion & effort*\n\n"
                            "Sur les modèles récents (Opus 4.6+, Sonnet 4.6, Fable 5), la "
                            "réflexion étendue se pilote par *adaptive thinking* :\n\n"
                            "• `thinking={\"type\": \"adaptive\"}` — le modèle décide combien réfléchir.\n"
                            "• L'ancien `budget_tokens` est *déprécié* (et rejeté en 400 sur "
                            "Opus 4.7/4.8 et Fable 5).\n"
                            "• `output_config={\"effort\": \"...\"}` (`low`→`max`) règle la "
                            "profondeur/le coût.\n\n"
                            "⚠️ `temperature` / `top_p` ne sont plus acceptés sur Opus 4.7/4.8 "
                            "et Fable 5 : on guide par le prompt."
                        ),
                        "quiz": _q(
                            "Comment activer la réflexion étendue sur Opus 4.8 ?",
                            ["A) budget_tokens=8000", "B) temperature=0", "C) thinking={'type':'adaptive'}", "D) top_p=0.9"],
                            "C",
                        ),
                    },
                ],
            },
            {
                "titre": "Module 4 — Tool use (function calling)",
                "lecons": [
                    {
                        "titre": "Définir un outil",
                        "contenu": (
                            "🛠️ *Module 4 · Leçon 1 — Définir un outil*\n\n"
                            "Un outil se décrit par 3 choses :\n\n"
                            "• `name` — nom clair (`get_weather`).\n"
                            "• `description` — *quand* et pourquoi l'appeler (décisif !).\n"
                            "• `input_schema` — un schéma JSON des paramètres.\n\n"
                            "```\n"
                            "{\n"
                            "  \"name\": \"get_weather\",\n"
                            "  \"description\": \"Météo actuelle d'une ville\",\n"
                            "  \"input_schema\": {\"type\": \"object\",\n"
                            "    \"properties\": {\"ville\": {\"type\": \"string\"}},\n"
                            "    \"required\": [\"ville\"]}\n"
                            "}\n"
                            "```\n"
                            "🎯 Une bonne `description` (le *quand* appeler) améliore nettement le déclenchement."
                        ),
                        "quiz": _q(
                            "Quel champ décrit les paramètres d'un outil ?",
                            ["A) input_schema", "B) max_tokens", "C) system", "D) stop_reason"],
                            "A",
                        ),
                    },
                    {
                        "titre": "La boucle agentique",
                        "contenu": (
                            "🛠️ *Module 4 · Leçon 2 — La boucle tool use*\n\n"
                            "Le cycle :\n"
                            "1. Le modèle renvoie un bloc `tool_use` (`stop_reason=tool_use`).\n"
                            "2. *Ton* code exécute l'outil.\n"
                            "3. Tu renvoies un bloc `tool_result` (avec le `tool_use_id` correspondant).\n"
                            "4. Le modèle continue, jusqu'à `end_turn`.\n\n"
                            "💡 En *parallèle* : si le modèle demande plusieurs outils, renvoie "
                            "tous les `tool_result` dans *un seul* message `user`.\n"
                            "🔒 Les outils à effet de bord (envoi, suppression…) méritent une "
                            "validation/confirmation côté harness."
                        ),
                        "quiz": _q(
                            "Plusieurs tool_result pour des appels parallèles se renvoient :",
                            ["A) un message chacun", "B) dans un seul message user", "C) en system", "D) on en garde un seul"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Outils côté serveur",
                        "contenu": (
                            "🛠️ *Module 4 · Leçon 3 — Outils serveur*\n\n"
                            "Certains outils tournent *chez Anthropic*, sans boucle côté client :\n\n"
                            "• *Web search* / *web fetch* — recherche/lecture web avec citations.\n"
                            "• *Code execution* — exécution de code en bac à sable.\n\n"
                            "On les *déclare* dans `tools` et le modèle s'en sert tout seul ; "
                            "les résultats reviennent comme blocs de contenu.\n\n"
                            "⚠️ Une erreur d'outil serveur ne lève pas d'exception : elle revient "
                            "en HTTP 200 dans un bloc résultat — il faut la tester."
                        ),
                        "quiz": _q(
                            "Un outil « côté serveur » (web search, code execution) :",
                            ["A) s'exécute chez Anthropic", "B) tourne dans ton code", "C) nécessite MCP", "D) est payant à part toujours"],
                            "A",
                        ),
                    },
                ],
            },
            {
                "titre": "Module 5 — Prompt caching",
                "lecons": [
                    {
                        "titre": "Principe du cache",
                        "contenu": (
                            "⚡ *Module 5 · Leçon 1 — Prompt caching*\n\n"
                            "Le cache réduit fortement coût et latence sur le contenu répété.\n\n"
                            "*L'invariant clé :* le cache est un *préfixe exact*. Le moindre octet "
                            "modifié dans le préfixe invalide tout ce qui suit.\n\n"
                            "Ordre de rendu : `tools` → `system` → `messages`.\n"
                            "On pose un point de cache avec `cache_control={\"type\": \"ephemeral\"}` "
                            "sur le dernier bloc *stable*.\n\n"
                            "🎯 Stable d'abord, volatile à la fin."
                        ),
                        "quiz": _q(
                            "Le prompt caching repose sur :",
                            ["A) une recherche floue", "B) un préfixe exact", "C) le hasard", "D) la température"],
                            "B",
                        ),
                    },
                    {
                        "titre": "Invalidations & vérification",
                        "contenu": (
                            "⚡ *Module 5 · Leçon 2 — Pièges du cache*\n\n"
                            "Ce qui *casse* silencieusement le cache :\n"
                            "• un `datetime.now()` ou un UUID en tête de `system`,\n"
                            "• un JSON sérialisé sans clés triées,\n"
                            "• un jeu d'outils qui change (les `tools` sont en position 0),\n"
                            "• changer de modèle (le cache est par modèle).\n\n"
                            "🔎 Vérifie avec `usage.cache_read_input_tokens` : s'il reste à 0 sur "
                            "des requêtes au préfixe identique, un invalidateur silencieux agit.\n\n"
                            "💡 Mets le contenu dynamique *après* le dernier point de cache."
                        ),
                        "quiz": _q(
                            "Comment vérifier qu'un cache est bien lu ?",
                            ["A) usage.cache_read_input_tokens > 0", "B) stop_reason=cache", "C) max_tokens=0", "D) impossible"],
                            "A",
                        ),
                    },
                ],
            },
            {
                "titre": "Module 6 — Agents & MCP",
                "lecons": [
                    {
                        "titre": "Construire un agent",
                        "contenu": (
                            "🤖 *Module 6 · Leçon 1 — Agents*\n\n"
                            "Choisis le niveau le plus simple qui suffit :\n"
                            "• *Un seul appel* — classification, résumé, Q/R.\n"
                            "• *Workflow* — pipeline multi-étapes piloté par ton code + tool use.\n"
                            "• *Agent* — le modèle décide sa trajectoire (boucle agentique, tes outils).\n"
                            "• *Managed Agents* — Anthropic exécute la boucle et héberge le bac "
                            "à sable des outils.\n\n"
                            "🎯 Avant de faire un agent : la tâche est-elle complexe, à forte "
                            "valeur, faisable, et les erreurs récupérables ? Sinon, reste simple."
                        ),
                        "quiz": _q(
                            "Pour une simple extraction d'info, le bon niveau est :",
                            ["A) un agent autonome", "B) Managed Agents", "C) un seul appel API", "D) multi-agents"],
                            "C",
                        ),
                    },
                    {
                        "titre": "MCP (Model Context Protocol)",
                        "contenu": (
                            "🤖 *Module 6 · Leçon 2 — MCP*\n\n"
                            "Le *MCP* (Model Context Protocol) standardise la connexion d'un LLM "
                            "à des capacités externes (serveurs d'outils : GitHub, Linear, etc.).\n\n"
                            "Côté API Messages, le *connecteur MCP* demande *deux* choses ensemble :\n"
                            "• `mcp_servers` — la déclaration du serveur (`type`, `url`, `name`), *sans* secret.\n"
                            "• un `tools` contenant un `mcp_toolset` qui référence ce serveur par son nom.\n\n"
                            "🔒 Les identifiants (auth) ne vont *pas* dans la déclaration du serveur "
                            "— ils passent par un coffre (vault), jamais dans le prompt."
                        ),
                        "quiz": _q(
                            "À quoi sert MCP ?",
                            ["A) compresser les tokens", "B) standardiser la connexion à des outils/serveurs externes", "C) accélérer le streaming", "D) remplacer le system prompt"],
                            "B",
                        ),
                    },
                ],
            },
        ],
        "examen": {
            "seuil": 0.8,  # 80 % pour être déclaré « prêt »
            "questions": [
                _q(
                    "Quel id de modèle correspond à l'Opus le plus récent vu dans la formation ?",
                    ["A) claude-opus-4-8", "B) claude-3-opus", "C) opus-latest", "D) claude-opus-4-8-20251101"],
                    "A",
                ),
                _q(
                    "L'API Messages est :",
                    ["A) avec état (mémorise seule)", "B) sans état (on renvoie l'historique)", "C) uniquement en streaming", "D) limitée à 1 tour"],
                    "B",
                ),
                _q(
                    "Sur Opus 4.8, pour activer la réflexion étendue on utilise :",
                    ["A) budget_tokens", "B) temperature", "C) thinking={'type':'adaptive'}", "D) top_k"],
                    "C",
                ),
                _q(
                    "Le champ décisif pour qu'un outil soit bien déclenché est souvent :",
                    ["A) son name seul", "B) sa description (quand l'appeler)", "C) max_tokens", "D) le modèle"],
                    "B",
                ),
                _q(
                    "Le prompt caching fonctionne sur la base d'un :",
                    ["A) préfixe exact", "B) résumé", "C) embedding", "D) hash aléatoire"],
                    "A",
                ),
                _q(
                    "Pour forcer une sortie JSON valide sur un modèle récent :",
                    ["A) prefill de l'assistant", "B) output_config.format", "C) stop_sequence", "D) température 0"],
                    "B",
                ),
                _q(
                    "Plusieurs résultats d'outils appelés en parallèle se renvoient :",
                    ["A) dans un seul message user", "B) un message chacun", "C) en system", "D) on ignore les surplus"],
                    "A",
                ),
                _q(
                    "Le connecteur MCP exige :",
                    ["A) seulement mcp_servers", "B) mcp_servers + un mcp_toolset qui le référence", "C) un prefill", "D) budget_tokens"],
                    "B",
                ),
                _q(
                    "Pour compter les tokens d'un texte pour Claude :",
                    ["A) tiktoken", "B) count_tokens du SDK", "C) len(texte)//4", "D) impossible"],
                    "B",
                ),
                _q(
                    "Avant de lire le contenu d'une réponse, on vérifie toujours :",
                    ["A) max_tokens", "B) stop_reason", "C) la température", "D) le cache"],
                    "B",
                ),
            ],
        },
    },
}


# ---------- Helpers ----------

def list_certifications():
    """[(cert_id, titre, description), ...]"""
    return [(cid, c["titre"], c["description"]) for cid, c in CERTIFICATIONS.items()]


def get_certification(cert_id):
    return CERTIFICATIONS.get(cert_id)


def total_lecons(cert_id):
    cert = CERTIFICATIONS.get(cert_id)
    if not cert:
        return 0
    return sum(len(m["lecons"]) for m in cert["modules"])


def get_lecon(cert_id, index):
    """Retourne (module, lecon, position_globale, total) ou None si index hors borne."""
    cert = CERTIFICATIONS.get(cert_id)
    if not cert:
        return None
    pos = 0
    for module in cert["modules"]:
        for lecon in module["lecons"]:
            if pos == index:
                return module, lecon, pos, total_lecons(cert_id)
            pos += 1
    return None


def get_examen(cert_id):
    cert = CERTIFICATIONS.get(cert_id)
    return cert["examen"] if cert else None
