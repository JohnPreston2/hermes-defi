#!/usr/bin/env python3
"""maintenance/textes.py - outils de la routine cloud « Planches 3D - maintenance Haiku » (14/10/2026).
Vit sur la branche claude/maintenance-planches ; lit les donnees de main (le depot clone).

  python3 maintenance/textes.py a_traduire            -> /tmp/a_traduire.json : textes affiches pas encore traduits
  python3 maintenance/textes.py verifier FICHIER      -> verifie les traductions de Haiku, les range dans
                                                         maintenance/traductions_proposees.json
  python3 maintenance/textes.py relecture FICHIER     -> verifie la forme de la relecture des captures, la range
                                                         dans maintenance/relecture.json

Regle (la meme que sur le serveur, qui verifie une seconde fois avant de publier) : une traduction n'est gardee
que si chaque nombre de l'original s'y retrouve et qu'aucun n'y est ajoute ; longueur 0,5 a 2,4 fois l'original.
"""
import datetime
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPOSEES = os.path.join(RACINE, 'maintenance', 'traductions_proposees.json')
RELECTURE = os.path.join(RACINE, 'maintenance', 'relecture.json')
CHAMPS_COHORTE = ('mecanisme', 'lignee_declaree', 'sortie_si', 'entre_si', 'commentaire', 'pourquoi')
FR = re.compile(r"\b(le|la|les|des|du|une|est|sont|pour|avec|dans|sur|qui|que|pas|aux|ce|cette|leur|selon|depuis)\b", re.I)
EN = re.compile(r"\b(the|and|is|are|of|with|for|on|by|to|from|as|its|this|that|will|has|have|after|into)\b", re.I)
TYPES = ('texte_coupe', 'chevauchement', 'sans_nom', 'zone_vide', 'contradiction', 'anglais', 'autre')


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc)


def lire(p, defaut=None):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return defaut


def ecrire(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(p + '.tmp', p)


def collecter():
    """Les textes bruts de l'agent que la page des planches affiche aujourd'hui."""
    out = {}

    def add(t, ou):
        if isinstance(t, str) and t.strip() and len(t) < 4000:
            out.setdefault(t.strip(), ou)

    b = (lire(os.path.join(RACINE, 'defi.json'), {}) or {}).get('blocks') or {}
    for x in ((b.get('theses') or {}).get('v') or {}).get('theses') or []:
        add(x.get('kill'), 'these')
    for x in ((b.get('wakes') or {}).get('v') or {}).get('items') or []:
        add(x.get('summary'), 'analyse')
    for g in ((b.get('fil_48h') or {}).get('v') or {}).get('groupes') or []:
        for x in g.get('items') or []:
            add(x.get('headline'), 'fil')
    for x in ((b.get('hot_news') or {}).get('v') or {}).get('news') or []:
        add(x.get('headline'), 'fil')
    for v in (lire(os.path.join(RACINE, 'planches', 'planches.json'), {}) or {}).values():
        if isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    for a in it.get('articles') or []:
                        add(a.get('t'), 'article')

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in CHAMPS_COHORTE and isinstance(v, str):
                    add(v, 'cohorte')
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(lire(os.path.join(RACINE, 'rapport', 'cohorte.json'), {}))
    return out


def deja_francais(t):
    return len(FR.findall(t)) >= 3 and not EN.search(t)


def nombres(t):
    s = t.replace(' ', ' ').replace('\xa0', ' ')
    s = re.sub(r'(?<=\d)[ ,](?=\d{3}\b)', '', s)
    s = re.sub(r'(?<=\d),(?=\d)', '.', s)
    return sorted(re.findall(r'\d+(?:\.\d+)?', s))


def verifier_une(orig, fr):
    if not fr or not fr.strip():
        return 'traduction vide'
    if '\n' in fr.strip() and '\n' not in orig:
        return 'plusieurs lignes'
    r = len(fr) / max(1, len(orig))
    if r < 0.5 or r > 2.4:
        return 'longueur anormale (%.1f fois l’original)' % r
    a, b = nombres(orig), nombres(fr)
    if a != b:
        return 'nombres différents : %s contre %s' % (' '.join(a) or '-', ' '.join(b) or '-')
    return None


def a_traduire():
    textes = collecter()
    pub = ((lire(os.path.join(RACINE, 'planches', 'traductions.json'), {}) or {}).get('t')) or {}
    prop = lire(PROPOSEES, {}) or {}
    liste = []
    for t, ou in textes.items():
        if t in pub or deja_francais(t):
            continue
        e = prop.get(t) or {}
        if e.get('statut') in ('ok', 'fr'):
            continue
        liste.append({'id': len(liste) + 1, 'origine': ou, 'texte': t})
    with open('/tmp/a_traduire.json', 'w', encoding='utf-8') as f:
        json.dump(liste, f, ensure_ascii=False, indent=1)
    print('%d textes affichés ; %d à traduire -> /tmp/a_traduire.json' % (len(textes), len(liste)))


def verifier(fichier):
    """FICHIER : [{"id": n, "langue": "fr"|"en"|"autre", "fr": "..."}], ids de /tmp/a_traduire.json."""
    liste = {x['id']: x['texte'] for x in lire('/tmp/a_traduire.json', [])}
    rep = lire(fichier)
    if not isinstance(rep, list):
        print('ARRET : %s doit contenir une liste JSON' % fichier)
        sys.exit(1)
    prop = lire(PROPOSEES, {}) or {}
    quand = maintenant().isoformat(timespec='seconds').replace('+00:00', 'Z')
    ok = refus = deja = 0
    refuses = []
    for x in rep:
        t = liste.get(x.get('id'))
        if not t:
            continue
        if x.get('langue') == 'fr':
            prop[t] = {'statut': 'fr', 'quand': quand}
            deja += 1
            continue
        m = verifier_une(t, x.get('fr') or '')
        if m:
            prop[t] = {'statut': 'refus', 'motif': m, 'propose': x.get('fr'), 'quand': quand}
            refus += 1
            refuses.append((x.get('id'), m))
        else:
            prop[t] = {'statut': 'ok', 'fr': x['fr'].strip(), 'quand': quand}
            ok += 1
    # on ne garde que les textes encore affiches (plus ceux des 30 derniers jours)
    affiches = set(collecter())
    limite = (maintenant() - datetime.timedelta(days=30)).isoformat()
    prop = {t: e for t, e in prop.items() if t in affiches or e.get('quand', '') >= limite}
    ecrire(PROPOSEES, prop)
    print('%d acceptées, %d refusées, %d déjà en français ; %d manquantes dans la réponse' % (ok, refus, deja, len(liste) - ok - refus - deja))
    for i, m in refuses[:20]:
        print('  refusée [%s] : %s' % (i, m))


def relecture(fichier):
    """FICHIER : {"defauts": [{"vue", "ecran", "type", "gravite", "constat"}]}."""
    j = lire(fichier)
    vues = lire('/tmp/captures/vues.json', []) or []
    noms = {v.get('nom') for v in vues}
    if not isinstance(j, dict) or not isinstance(j.get('defauts'), list):
        print('ARRET : %s doit contenir {"defauts": [...]}' % fichier)
        sys.exit(1)
    net, ecartes = [], 0
    for d in j['defauts']:
        if not isinstance(d, dict) or d.get('ecran') not in ('ordinateur', 'telephone') or d.get('type') not in TYPES \
                or d.get('gravite') not in ('bloquant', 'gene') or not str(d.get('constat', '')).strip() or d.get('vue') not in noms:
            ecartes += 1
            continue
        net.append({k: d[k] for k in ('vue', 'ecran', 'type', 'gravite', 'constat')})
    ecrire(RELECTURE, {'jour': maintenant().strftime('%Y-%m-%d'), 'quand': maintenant().isoformat(timespec='seconds').replace('+00:00', 'Z'),
                       'modele': 'claude-haiku-5-5 (routine cloud)', 'n_captures': len(vues), 'defauts': net})
    print('%d constats gardés, %d écartés (forme invalide ou vue inconnue) -> maintenance/relecture.json' % (len(net), ecartes))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'a_traduire':
        a_traduire()
    elif cmd == 'verifier' and len(sys.argv) > 2:
        verifier(sys.argv[2])
    elif cmd == 'relecture' and len(sys.argv) > 2:
        relecture(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(2)
