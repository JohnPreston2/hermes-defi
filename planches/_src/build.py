# Version tableau de bord de la page des planches : build/planches/index.html
# Différences avec la version artifact : données lues dans planches.json, logos dans logos/,
# moteur 3D copié dans vendor/ (aucun appel extérieur), polices du système, pas de couleur pour les
# hausses et les baisses (règle du tableau de bord : le signe vit dans le libellé), retour vers le tableau de bord.
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'top10.html')
OUT = os.path.join(os.path.dirname(HERE), 'index.html')
t = open(SRC, encoding='utf-8').read(); n = 0
def rep(a, b, regex=False):
    global t, n
    if regex:
        t2 = re.sub(a, b, t, count=1, flags=re.S)
        assert t2 != t, ('ABSENT', a[:80]); t = t2
    else:
        assert a in t, ('ABSENT', a[:80]); t = t.replace(a, b, 1)
    n += 1

rep(r'<!--FONTS-->.*?<!--/FONTS-->', '', regex=True)
rep("<title>Top 10 en relief</title>", "<title>Planches 3D — Hermes DeFi</title>")
rep("--display: 'Bodoni Moda', 'Didot', Georgia, serif;", "--display: 'Didot', 'Bodoni 72', 'Bodoni MT', ui-serif, 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif;")
rep("--ui: 'Geist', 'Segoe UI', system-ui, sans-serif;", "--ui: 'Segoe UI Variable Text', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;")
rep("--mono: 'Geist Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace;", "--mono: ui-monospace, 'Cascadia Mono', 'SF Mono', 'JetBrains Mono', Consolas, monospace;")
rep('"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"',
    '"three":"./vendor/three/build/three.module.min.js","three/addons/":"./vendor/three/examples/jsm/"')
rep(r'<!--BRAND-->.*?<!--/BRAND-->', '<a href="../">← <b>Hermes DeFi</b></a> · planches 3D', regex=True)
rep("@media (max-width: 1100px) { .hint { display: none; } }", ".up, .down { color: inherit; }\n@media (max-width: 1100px) { .hint { display: none; } }")
# garde-fous : plus aucun appel extérieur, données non embarquées
assert 'googleapis' not in t and 'jsdelivr' not in t and 'cdnjs' not in t, 'appel extérieur restant'
assert '/*__DATA__*/null' in t and '/*__LOGOS__*/null' in t and '/*__HERMES__*/null' in t
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8', newline='\n').write(t)
print('index.html', len(t) // 1024, 'Ko ;', n, 'remplacements ; liens https restants :', sorted(set(re.findall(r'https://[a-z0-9.-]+', t))))
