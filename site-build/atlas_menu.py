# Ajoute le lien Atlas aux menus du site apres la generation des pages.
# Le build echoue si un des menus attendus est introuvable : la production reste alors inchangee.
import glob
import io
import os

BS = chr(92)
Q = BS + '"'
NL = BS + 'n'


def lire(chemin):
    return io.open(chemin, encoding='utf-8').read()


def ecrire(chemin, texte):
    io.open(chemin, 'w', encoding='utf-8').write(texte)


def une_fois(s, ancien, nouveau, nom):
    n = s.count(ancien)
    assert n == 1, nom + ' : ' + str(n) + ' occurrence(s)'
    return s.replace(ancien, nouveau)


def accueil(s):
    plus = '<a href=' + Q + '#plus' + Q + ' onClick'
    a = '))}' + NL + '          ' + plus
    lien = '<a href=' + Q + '/atlas' + Q + " style={{color:'inherit', textDecoration:'none'}}>Atlas<" + BS + 'u002Fa>'
    s = une_fois(s, a, '))}' + NL + '          ' + lien + NL + '          ' + plus, 'menu ordinateur')
    b = "add('div', 'gfm-k', W.prod)"
    s = une_fois(s, b, "add('a', '', 'Atlas', '/atlas')" + NL + '  ' + b, 'menu mobile')
    return s


def page(s):
    lien = '<a href="/atlas">Atlas</a>'
    s = s.replace('</div><div class="nav-r">', lien + '</div><div class="nav-r">', 1)
    s = s.replace('<a class="gf-menu-cta"', lien + '<a class="gf-menu-cta"', 1)
    return s


app = os.path.join('public', 'app-src.html')
ecrire(app, accueil(lire(app)))

n = 0
for chemin in glob.glob(os.path.join('public', '**', '*.html'), recursive=True):
    if chemin == app:
        continue
    if os.sep + 'atlas' + os.sep in chemin:
        continue
    s = lire(chemin)
    if '<div class="gf-menu-panel">' not in s:
        continue
    t = page(s)
    assert t.count('href="/atlas"') >= 2, chemin
    ecrire(chemin, t)
    n += 1
assert n >= 8, 'pages modifiees : ' + str(n)

plan = os.path.join('public', 'sitemap.xml')
ecrire(plan, une_fois(lire(plan), '</urlset>', '<url><loc>https://greenfield.plus/atlas</loc></url></urlset>', 'sitemap'))
print('Lien Atlas ajoute : accueil, ' + str(n) + ' pages, sitemap')
