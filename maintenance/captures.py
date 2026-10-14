#!/usr/bin/env python3
"""maintenance/captures.py - photographie les 17 vues des planches 3D (ordinateur 1440x900 puis telephone 390x844)
a partir du depot clone, servi en local. Sortie : /tmp/captures/<ecran>_<vue>.jpg + /tmp/captures/vues.json
(nom de la vue, ecran, fichier, titre, phrase sous le titre, legende, etiquettes visibles, erreurs JavaScript).

Sans carte graphique, la scene 3D est dessinee en logiciel, tres lentement : la page croit avoir une densite de
pixels plus basse (le texte reste net), la boucle d'animation est mise en pause pendant chaque capture, et la
composition de Chrome est logicielle (capture en quelques secondes au lieu de 30 a 47). Mesure du 14/10/2026.
Usage : python3 maintenance/captures.py [vue1,vue2]
"""
import base64
import json
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = '/tmp/captures'
PORT = 8765
ECRANS = [
    ('ordinateur', dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=1), 0.5),
    ('telephone', dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2), 0.75),
]
INIT = """window.__DTCAP = 2; window.__NOADAPT = 1;
(() => { Object.defineProperty(window, 'devicePixelRatio', { get: () => %s, configurable: true });
  const raf = window.requestAnimationFrame.bind(window), q = [];
  window.requestAnimationFrame = (cb) => { if (window.__PAUSE) { q.push(cb); return 0; } return raf(cb); };
  window.__RESUME = () => { window.__PAUSE = false; q.splice(0).forEach((cb) => raf(cb)); }; })();"""
SONDE = r"""() => { const ui = window.__ui, k = ui.state.pl, P = ui.PL[k];
  const t = (id) => { const e = document.getElementById(id); return e ? e.innerText.replace(/\s+/g, ' ').trim() : ''; };
  const vis = [...document.querySelectorAll('.lset:not([hidden]) .lb')].filter(e => +e.style.opacity > .5).map(e => e.textContent.replace(/\s+/g, ' ').trim());
  return { k, onglet: P.tab || k, vue: P.view || '', titre: t('title'), sous_titre: t('insight'), legende: t('legend'), etiquettes: vis.slice(0, 40) }; }"""


def main():
    voulues = set(filter(None, (sys.argv[1] if len(sys.argv) > 1 else '').split(',')))
    os.makedirs(OUT, exist_ok=True)
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=RACINE,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    url = 'http://127.0.0.1:%d/planches/' % PORT
    vues, t_debut = [], time.time()
    try:
        with sync_playwright() as p:
            # le cloud bloque le telechargement des navigateurs de Playwright, mais un Chromium y est preinstalle
            exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
            b = p.chromium.launch(executable_path=exe, args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-compositing'])
            for ecran, kw, dpr in ECRANS:
                ctx = b.new_context(**kw)
                pg = ctx.new_page()
                pg.set_default_timeout(120000)
                pg.add_init_script(INIT % dpr)
                cour = {'k': 'chargement'}
                errs = []
                pg.on('pageerror', lambda e: errs.append((cour['k'], str(e)[:200])))
                pg.goto(url + '#crypto', wait_until='domcontentloaded')
                pg.wait_for_function('() => window.__ui && window.__ui.api && window.__ui.ALLK', polling=250)
                cdp = ctx.new_cdp_session(pg)
                cles = [k for k in pg.evaluate('() => window.__ui.ALLK.slice()') if not voulues or k in voulues or k.split('-')[0] in voulues]
                for i, k in enumerate(cles):
                    cour['k'] = k
                    t0 = time.time()
                    if i or k != 'crypto':
                        pg.evaluate('(k) => { location.hash = k; }', k)
                    try:
                        pg.wait_for_function('(k) => window.__ui.api.active === k', arg=k, polling=250)
                        ts = pg.evaluate('() => window.__ui.api.t')
                        pg.wait_for_function('([a, d]) => window.__ui.api.t - a > d', arg=[ts, 3.0], polling=250)
                    except Exception as e:
                        errs.append((k, 'la vue ne s’affiche pas en 2 minutes (%s)' % type(e).__name__))
                    s = pg.evaluate(SONDE)
                    pg.evaluate('() => { window.__PAUSE = true; }')
                    pg.wait_for_timeout(300)
                    f = os.path.join(OUT, '%s_%s.jpg' % (ecran, k))
                    r = cdp.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': 82, 'optimizeForSpeed': True})
                    with open(f, 'wb') as fh:
                        fh.write(base64.b64decode(r['data']))
                    pg.evaluate('() => window.__RESUME()')
                    s.update({'nom': s['onglet'] + (' · ' + s['vue'] if s['vue'] and s['vue'] != s['onglet'] else ''), 'ecran': ecran, 'fichier': f,
                              'erreurs': [m for kk, m in errs if kk == k]})
                    vues.append(s)
                    print('%s %-14s %3.0f s  %s' % (ecran, k, time.time() - t0, ('ERREURS ' + ' | '.join(s['erreurs'])) if s['erreurs'] else ''), flush=True)
                ctx.close()
            b.close()
    finally:
        srv.terminate()
    with open(os.path.join(OUT, 'vues.json'), 'w', encoding='utf-8') as fh:
        json.dump(vues, fh, ensure_ascii=False, indent=1)
    print('%d captures en %.0f s -> %s/vues.json' % (len(vues), time.time() - t_debut, OUT))


if __name__ == '__main__':
    main()
