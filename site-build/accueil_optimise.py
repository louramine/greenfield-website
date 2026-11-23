# Allege l'accueil et corrige plusieurs points de l'audit du site.
# A lancer en dernier, avec PYTHONPATH=.pydeps (Pillow).
#  1. Favicon : ajoute favicon-32.png et apple-touch-icon.png (180 px) et leurs balises.
#  2. Contraste : le gris attenue #6b8376 (4,18 sur le fond) devient #80988b (5,53).
#  3. Accueil : logo de 2821 px ramene a 84 px de haut, React en version production,
#     code JSX compile pendant le build au lieu de Babel dans le navigateur du visiteur.
#  4. Mobile : le formulaire de contact passe sur une colonne sous 680 px.
#  5. Barre flottante mobile : elle ouvre WhatsApp, son texte le dit desormais.
# Le build echoue si un emplacement attendu est introuvable. Les etapes qui dependent du reseau
# ou de Node sont sautees (avec un message) si elles ne peuvent pas se faire.
import base64
import glob
import gzip
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import urllib.request

from PIL import Image, ImageDraw

BS = chr(92)
ANCIEN_GRIS = '#6b8376'
NOUVEAU_GRIS = '#80988b'
BABEL = 'd0411292-6398-41d8-9751-05a172af20af'
REACT = 'f209b1e5-cd54-4e74-9540-baf3ae406732'
REACT_DOM = '87f09f10-b813-46db-b83c-1b9d7354404d'
LOGO = '1b31e2a4-0d52-44a7-98c6-19d5aa93ac84'
VERSION_REACT = '18.3.1'


def lire(chemin):
    return io.open(chemin, encoding='utf-8').read()


def ecrire(chemin, texte):
    io.open(chemin, 'w', encoding='utf-8').write(texte)


# 1. Favicons PNG dessines a partir du meme motif que favicon.svg (carre arrondi, croix menthe)
def icone(taille, coins):
    k = taille / 64
    im = Image.new('RGBA', (taille, taille), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, taille - 1, taille - 1], radius=round(coins * k), fill='#0b1f13')
    d.rectangle([round(28 * k), round(14 * k), round(36 * k) - 1, round(50 * k) - 1], fill='#86dab0')
    d.rectangle([round(14 * k), round(28 * k), round(50 * k) - 1, round(36 * k) - 1], fill='#86dab0')
    return im


icone(32, 12).save(os.path.join('public', 'favicon-32.png'), optimize=True)
apple = Image.new('RGB', (180, 180), '#0b1f13')
apple.paste(icone(180, 0), (0, 0))
apple.save(os.path.join('public', 'apple-touch-icon.png'), optimize=True)
BALISES = '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'

n = 0
for chemin in glob.glob(os.path.join('public', '**', '*.html'), recursive=True):
    s = lire(chemin)
    t = s
    if 'rel="apple-touch-icon"' not in t and '<link rel="icon"' in t:
        i = t.find('<link rel="icon"')
        j = t.find('>', i) + 1
        t = t[:j] + BALISES + t[j:]
        n += 1
    t = t.replace(ANCIEN_GRIS, NOUVEAU_GRIS)
    if t != s:
        ecrire(chemin, t)
assert n >= 10, 'pages avec favicons : ' + str(n)

# 2. Contraste dans les feuilles de style
for chemin in glob.glob(os.path.join('public', '**', '*.css'), recursive=True):
    s = lire(chemin)
    if ANCIEN_GRIS in s:
        ecrire(chemin, s.replace(ANCIEN_GRIS, NOUVEAU_GRIS))

# 3. Accueil
app = os.path.join('public', 'app-src.html')
s = lire(app)
s = s.replace(ANCIEN_GRIS, NOUVEAU_GRIS)


def bloc(s, typ):
    debut = '<script type="__bundler/' + typ + '">'
    i = s.find(debut)
    assert i >= 0, typ
    i += len(debut)
    j = s.find('</script>', i)
    return i, j


i, j = bloc(s, 'manifest')
manifeste = json.loads(s[i:j])
k, m = bloc(s, 'template')
modele = json.loads(s[k:m])
avant = len(s)


def donnees(cle):
    v = manifeste[cle]
    b = base64.b64decode(v['data'])
    return gzip.decompress(b) if v.get('compressed') else b


def ranger(cle, octets, compresser):
    v = manifeste[cle]
    if compresser:
        v['data'] = base64.b64encode(gzip.compress(octets, 9)).decode('ascii')
        v['compressed'] = True
    else:
        v['data'] = base64.b64encode(octets).decode('ascii')
        v['compressed'] = False


# 3a. Logo : affiche a 28 px de haut, stocke en 2821 px. On garde 3 fois la hauteur affichee.
assert LOGO in manifeste, 'logo'
im = Image.open(io.BytesIO(donnees(LOGO)))
if im.size[1] > 84:
    im = im.resize((round(im.size[0] * 84 / im.size[1]), 84), Image.LANCZOS)
    sortie = io.BytesIO()
    im.save(sortie, 'PNG', optimize=True)
    ranger(LOGO, sortie.getvalue(), False)
    print('Logo de l accueil : ' + str(im.size[0]) + ' x 84 px')


# 3b. React : version production a la place de la version de developpement
def paquet(nom, fichier):
    url = 'https://registry.npmjs.org/' + nom + '/-/' + nom + '-' + VERSION_REACT + '.tgz'
    with urllib.request.urlopen(url, timeout=60) as r:
        tgz = r.read()
    with tarfile.open(fileobj=io.BytesIO(tgz), mode='r:gz') as tf:
        return tf.extractfile('package/umd/' + fichier).read()


assert donnees(REACT).decode('utf-8', 'replace').find('react.development.js') >= 0, 'react'
assert donnees(REACT_DOM).decode('utf-8', 'replace').find('react-dom.development.js') >= 0, 'react-dom'
try:
    r1 = paquet('react', 'react.production.min.js')
    r2 = paquet('react-dom', 'react-dom.production.min.js')
    ranger(REACT, r1, True)
    ranger(REACT_DOM, r2, True)
    print('React ' + VERSION_REACT + ' en version production')
except Exception as e:
    print('React production non telecharge, version de developpement conservee : ' + str(e))

# 5. Barre flottante mobile : le texte annonce WhatsApp
barre = ('<a className="mobile-cta-bar gf-btn gf-btn-primary" href="https://wa.me/212776250052" target="_blank" rel="noopener">\n'
         "        {T('Prendre contact')} <span>{ARR}</span>")
assert modele.count(barre) == 1, 'barre mobile'
assert 'const gfLangue' in modele, 'formulaire_contact.py doit etre lance avant'
modele = modele.replace(barre, barre.replace(
    "{T('Prendre contact')}",
    "{({fr:'Écrire sur WhatsApp', en:'Message us on WhatsApp', ar:'راسلونا عبر واتساب'})[gfLangue()]}"))


# 3c. JSX compile pendant le build avec le Babel deja embarque dans la page
OUVRE = '<script type="text/babel" data-presets="react">'
assert modele.count(OUVRE) == 2, 'scripts babel : ' + str(modele.count(OUVRE))
balise_babel = re.search('<script src="' + BABEL + '"[^>]*></script>', modele)
assert balise_babel, 'balise Babel'
codes = []
pos = 0
while OUVRE in modele[pos:]:
    a = modele.index(OUVRE, pos)
    b = modele.index('</script>', a)
    codes.append(modele[a + len(OUVRE):b])
    pos = b
dossier = tempfile.mkdtemp()
io.open(os.path.join(dossier, 'babel.js'), 'wb').write(donnees(BABEL))
for x, code in enumerate(codes):
    ecrire(os.path.join(dossier, 'in' + str(x) + '.jsx'), code)
compile_js = os.path.join(dossier, 'compile.js')
ecrire(compile_js, '\n'.join([
    "const fs = require('fs')",
    "const path = require('path')",
    "const dir = process.argv[2]",
    "const B = require(path.join(dir, 'babel.js'))",
    "for (const x of [...Array(Number(process.argv[3])).keys()]) {",
    "  const src = fs.readFileSync(path.join(dir, 'in' + x + '.jsx'), 'utf8')",
    "  const out = B.transform(src, { presets: ['react'] }).code",
    "  fs.writeFileSync(path.join(dir, 'out' + x + '.js'), out)",
    "}",
]))
try:
    subprocess.run(['node', compile_js, dossier, str(len(codes))], check=True, timeout=300)
    compiles = [lire(os.path.join(dossier, 'out' + str(x) + '.js')) for x in range(len(codes))]
    for c in compiles:
        assert '</script' not in c.lower()
    for code in codes:
        modele = modele.replace(OUVRE + code + '</script>', '', 1)
    modele = modele.replace(balise_babel.group(0), '', 1)
    fin = modele.rfind('</body>')
    assert fin >= 0, 'fin du body'
    ajout = ''.join('<script>' + c + '</script>' + chr(10) for c in compiles)
    modele = modele[:fin] + ajout + modele[fin:]
    del manifeste[BABEL]
    print('JSX compile pendant le build, Babel retire de la page')
except Exception as e:
    print('Compilation JSX impossible, Babel conserve : ' + str(e))

# 4. Formulaire sur une colonne en mobile (les champs qui couvrent 2 colonnes en creaient une seconde)
CSS = ('<style>'
       '@media (max-width:680px){section#contact form{grid-template-columns:1fr !important}}'
       '@media (max-width:680px){section#contact form > *{grid-column:1 / -1 !important}}'
       '@media (max-width:680px){section#contact form > div{border-inline-end:none !important}}'
       '</style>')
assert modele.count('</head>') >= 1, 'head'
modele = modele.replace('</head>', CSS + BALISES + '</head>', 1)



def json_page(obj):
    return json.dumps(obj, ensure_ascii=False).replace('</', '<' + BS + 'u002F')


k, m = bloc(s, 'template')
s = s[:k] + json_page(modele) + s[m:]
i, j = bloc(s, 'manifest')
s = s[:i] + json_page(manifeste) + s[j:]
ecrire(app, s)
print('Accueil : ' + str(round(avant / 1e6, 2)) + ' Mo avant, ' + str(round(len(s) / 1e6, 2)) + ' Mo apres')
