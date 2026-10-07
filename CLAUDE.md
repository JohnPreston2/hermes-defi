# Hermes DeFi — guide pour les sessions Claude Code

Ce dépôt est le site public du tableau de bord Hermes DeFi :
https://johnpreston2.github.io/hermes-defi/

Le propriétaire n'est pas développeur. Écris-lui en français simple, explique chaque terme technique
la première fois, et termine chaque demande de fusion par ce qui a changé à l'écran et comment tu l'as vérifié.

## Règle n° 1 : enrichir, jamais remplacer

Une session ici AJOUTE de la valeur au tableau de bord. Elle ne remplace pas ce qui existe.
- Ne supprime, ne réécris et ne déplace aucune section, aucun bloc, aucune planche existante.
- Un ajout doit pouvoir être retiré seul sans casser le reste (bloc séparé, repère de commentaire, style préfixé).
- Toute suppression ou refonte d'une partie existante demande l'accord explicite du propriétaire, écrit dans la demande.

## Qui écrit quoi

Un serveur de recherche (l'agent Hermes, hors d'atteinte depuis le cloud) produit les données et publie dans ce dépôt
toutes les 2 heures (à :53 UTC les heures paires). Les chiffres des planches (`planches/planches.json`) sont relevés
chaque heure et publiés aussi à :53 les heures impaires. Avant chaque publication, il récupère ce qui a été fusionné sur GitHub.

**Fichiers produits par le serveur — ne jamais les modifier :**
- `defi.json` (les blocs de données du tableau de bord) et `une.json`
- `planches/planches.json` et `planches/logos/`
- tout le dossier `rapport/` (rapports quotidiens, enquêtes, séries, veille des thèses)

**Fichiers que tu peux enrichir :**
- `index.html` : la page d'accueil, écrite à la main (aucun script ne la régénère).
- `planches/_src/top10.html` : la source des planches 3D. Après modification, lance
  `python3 planches/_src/build.py` : il régénère `planches/index.html`. **N'édite jamais `planches/index.html` à la main.**
  Cette source garde volontairement les liens externes de sa version d'origine (polices web, three.js sur un CDN) :
  `build.py` les remplace par les fichiers du site et refuse de produire une page qui en contiendrait encore.
  Ne les retire pas de la source.
- Un nouveau fichier ou dossier pour une nouvelle page, si l'ajout le justifie.

## Les règles du site (elles s'appliquent à tout ajout)

- **Aucun appel extérieur** : pas de bibliothèque sur un CDN, pas de police web, pas d'API tierce depuis le navigateur.
  Tout ce qui est chargé vient du site lui-même. three.js r170 est déjà copié dans `planches/vendor/three/`.
- **Une seule lecture des données sur l'accueil** : le script principal charge `defi.json` une fois et publie
  `window.__defiData` puis l'événement `defi:data`. Un ajout écoute cet événement au lieu de recharger le fichier.
- **Transcrire, jamais embellir** : un chiffre affiché est recopié tel quel de `defi.json`, avec sa date.
  S'il manque, écris « manquant » ; n'invente jamais une valeur de repli.
- **Pas de couleur pour les hausses et les baisses** : le signe vit dans le libellé (+ / −). Les couleurs d'état
  (tenue, ouverte, cassée…) sont toujours accompagnées d'un libellé.
- **Vocabulaire de recherche, pas de trading** : jamais « acheter », « vendre », « bullish », « bearish »,
  « objectif de cours », « signal ». On décrit des fondamentaux (valeur déposée, frais, revenus, capture, multiples).
- **Lisible partout** : thème clair et sombre (jetons de couleur dans `:root`), téléphone 375 px sans défilement
  horizontal, `prefers-reduced-motion` respecté, aucun texte visible sous 10,5 px.

**Deux exceptions existent déjà ; ce ne sont pas des défauts à corriger :**
- L'accueil contient des étiquettes de 9 à 10 px (19 réglages dans `index.html`). Ne les retouche pas sans demande ;
  la limite de 10,5 px vaut pour ce que tu ajoutes.
- La page des planches 3D est sombre seulement, par choix (un studio noir). Un ajout sur cette page suit son thème sombre.

## Livrer

1. Une branche, une demande de fusion petite et ciblée. Jamais de push direct sur `main`, jamais de `--force`.
2. Vérifie avant de livrer : sers le dépôt en local (`python3 -m http.server 8000` à la racine), ouvre
   `http://localhost:8000/` et `http://localhost:8000/planches/`, contrôle la console (zéro erreur) et le téléphone.
3. Dans la description : ce qui change à l'écran, ce qui n'a pas changé, comment c'est vérifié, comment le retirer.

**Vérifier dans un navigateur depuis le cloud.** Installe Playwright et Chromium :
`pip install playwright` puis `python3 -m playwright install --with-deps chromium`.
Les planches 3D ont besoin de WebGL : lance Chromium avec `--use-angle=swiftshader --enable-unsafe-swiftshader`,
charge la page avec `wait_until="commit"` (la boucle d'animation empêche l'évènement `load` d'arriver à temps),
et n'ouvre qu'une page 3D à la fois. Si l'installation échoue, arrête-toi et dis-le :
n'annonce jamais une vérification que tu n'as pas pu faire.

Après la fusion, GitHub Pages met environ une minute ; le serveur récupère la fusion à sa publication suivante.
Pour revenir en arrière : une nouvelle demande de fusion qui annule la précédente (`git revert`).
