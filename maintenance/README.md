# Maintenance des planches 3D par Claude Haiku (routines cloud)

Cette branche n'est **jamais fusionnée** dans `main`. Elle sert de boîte aux lettres entre deux routines
Claude Code dans le cloud (crédit de sessions cloud du propriétaire) et le serveur Hermes (delta).

| Fichier | Écrit par | Lu par |
|---|---|---|
| `maintenance/traductions_proposees.json` | routine « Planches 3D — traduction » (toutes les 2 h) | `planches_traduction.py` sur delta (chaque heure à :46) : revérifie chaque traduction, puis publie `planches/traductions.json` sur `main` |
| `maintenance/relecture.json` | routine « Planches 3D — relecture du matin » (chaque jour) | `planches_controle.py` sur delta (11 h 31, heure de Paris) : Telegram si un défaut bloquant revient deux matins de suite |

Règle de traduction, vérifiée deux fois par le code (ici, puis sur delta) : chaque nombre de l'original doit se
retrouver dans la traduction, aucun nombre ajouté, longueur entre 0,5 et 2,4 fois l'original.

Outils : `maintenance/textes.py` (textes à traduire, vérification, relecture) et `maintenance/captures.py`
(captures des 17 vues, ordinateur et téléphone, depuis le dépôt servi en local).
