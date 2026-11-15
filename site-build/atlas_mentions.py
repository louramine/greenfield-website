# Ajoute les mentions de la carte Greenfield Atlas dans le site, apres atlas_menu.py.
# Accueil (section Atlas), Programme Plus, Sourcing terrain, FAQ, Prix des terrains, llms.txt.
# Francais, anglais, arabe. Le build echoue si un emplacement attendu est introuvable.
import glob
import io
import os

BS = chr(92)
NL = chr(10)
PV = chr(59)

TXT = {
    'fr': {
        'h1': 'La carte du foncier, ',
        'h2': 'en accès libre',
        'p': 'Greenfield Atlas réunit sur une seule carte les terrains disponibles que nous suivons à Casablanca et environs. Filtrez par prix, superficie, secteur et zonage pour repérer en quelques minutes où se trouvent les opportunités. Les localisations sont volontairement approximatives : les fiches détaillées et les terrains off-market se découvrent en rendez-vous.',
        'b': 'Explorer la carte Atlas',
        'pt': 'La carte Atlas, en version complète',
        'pd': 'Le mode découverte de Greenfield Atlas est ouvert à tous, avec des localisations approximatives. Les clients Plus reçoivent leurs sélections sur une carte détaillée : contours exacts, superficies et prix, sur un lien personnel.',
        'pb': 'Voir le mode découverte',
        'lt': 'Carte Greenfield Atlas',
        'ld': 'Une vue d’ensemble des terrains disponibles par secteur, zonage et budget, consultable avant même le brief.',
        'fq': 'Peut-on voir les terrains disponibles sur une carte ?',
        'fa1': 'Oui. ',
        'fa2': ' est la carte interactive des terrains disponibles suivis par Greenfield+ à Casablanca et environs. Elle se consulte librement en mode découverte : chaque terrain y figure avec une localisation et une forme volontairement approximatives, et la carte se filtre par prix, superficie, secteur et zonage. Les fiches détaillées et les terrains off-market sont présentés sur rendez-vous.',
        'px': 'Voir les terrains disponibles sur la carte Atlas',
        'fl': '→',
    },
    'en': {
        'h1': 'The land map, ',
        'h2': 'open to all',
        'p': 'Greenfield Atlas brings together on a single map the available plots we track in Casablanca and the surrounding area. Filter by price, size, area and zoning to see in minutes where the opportunities are. Locations are deliberately approximate: detailed files and off-market plots are presented by appointment.',
        'b': 'Explore the Atlas map',
        'pt': 'The Atlas map, in full',
        'pd': 'The discovery mode of Greenfield Atlas is open to everyone, with approximate locations. Plus clients receive their shortlists on a detailed map: exact boundaries, sizes and prices, through a personal link.',
        'pb': 'See the discovery mode',
        'lt': 'Greenfield Atlas map',
        'ld': 'An overview of available plots by area, zoning and budget, open to you even before the brief.',
        'fq': 'Can I see the available plots on a map?',
        'fa1': 'Yes. ',
        'fa2': ' is the interactive map of the available plots tracked by Greenfield+ in Casablanca and the surrounding area. It is freely accessible in discovery mode: each plot appears with a deliberately approximate location and shape, and the map can be filtered by price, size, area and zoning. Detailed files and off-market plots are presented by appointment.',
        'px': 'See available plots on the Atlas map',
        'fl': '→',
    },
    'ar': {
        'h1': 'خريطة العقار، ',
        'h2': 'متاحة للجميع',
        'p': 'تجمع Greenfield Atlas في خريطة واحدة الأراضي المتاحة التي نتابعها في الدار البيضاء ونواحيها. يمكنكم التصفية حسب الثمن والمساحة والقطاع والتنطيق لتحديد مواقع الفرص في دقائق. المواقع تقريبية عن قصد: الملفات المفصلة والأراضي خارج السوق تُعرض خلال موعد.',
        'b': 'استكشاف خريطة Atlas',
        'pt': 'خريطة Atlas بنسختها الكاملة',
        'pd': 'وضع الاكتشاف في Greenfield Atlas مفتوح للجميع بمواقع تقريبية. أما عملاء Plus فيتوصلون باختياراتهم على خريطة مفصلة: الحدود الدقيقة والمساحات والأثمان، عبر رابط شخصي.',
        'pb': 'مشاهدة وضع الاكتشاف',
        'lt': 'خريطة Greenfield Atlas',
        'ld': 'نظرة شاملة على الأراضي المتاحة حسب القطاع والتنطيق والميزانية، متاحة حتى قبل تحديد الطلب.',
        'fq': 'هل يمكن الاطلاع على الأراضي المتاحة على خريطة؟',
        'fa1': 'نعم. ',
        'fa2': ' هي الخريطة التفاعلية للأراضي المتاحة التي تتابعها Greenfield+ في الدار البيضاء ونواحيها. يمكن تصفحها بحرية في وضع الاكتشاف: تظهر كل أرض بموقع وشكل تقريبيين عن قصد، ويمكن تصفية الخريطة حسب الثمن والمساحة والقطاع والتنطيق. أما الملفات المفصلة والأراضي خارج السوق فتُعرض خلال موعد.',
        'px': 'عرض الأراضي المتاحة على خريطة Atlas',
        'fl': '←',
    },
}
LANGUES = ['fr', 'en', 'ar']


def lire(chemin):
    return io.open(chemin, encoding='utf-8').read()


def ecrire(chemin, texte):
    io.open(chemin, 'w', encoding='utf-8').write(texte)


def une_fois(s, ancien, nouveau, nom):
    n = s.count(ancien)
    assert n == 1, nom + ' : ' + str(n) + ' occurrence(s)'
    return s.replace(ancien, nouveau)


def pour_app(texte):
    # Le code de l'accueil est range dans une chaine : guillemets, retours a la ligne et balises fermantes y sont echappes.
    return texte.replace('"', BS + '"').replace('</', '<' + BS + 'u002F').replace(NL, BS + 'n')


def objet_js(d, cles):
    return '{' + ', '.join(k + ":'" + d[k] + "'" for k in cles) + '}'


# 1. Accueil et Programme Plus (application)
CLES = ['h1', 'h2', 'p', 'b', 'pt', 'pd', 'pb']
for lang in LANGUES:
    for k in CLES:
        assert "'" not in TXT[lang][k], lang + ' ' + k

DEF = 'const ATL = {' + ', '.join(l + ':' + objet_js(TXT[l], CLES) for l in LANGUES) + '}' + NL + 'const AT = ATL[window.GF_LANG] ? ATL[window.GF_LANG] : ATL.fr' + NL

SECTION = '''      {/* ATLAS */}
      <section id="atlas" style={{padding:'96px 56px', borderTop:'1px solid var(--gf-line)'}}>
        <FadeIn delay={0}>
          <div className="gf-kicker">GREENFIELD ATLAS</div>
          <h2 className="gf-display" style={{fontSize:'clamp(40px,5vw,72px)', margin:'20px 0 24px'}}>{AT.h1}<span style={{color:'var(--gf-mint)'}}>{AT.h2}</span>.</h2>
          <p className="gf-body-lg" style={{maxWidth:720}}>{AT.p}</p>
          <div style={{marginTop:36}}>
            <a className="gf-btn gf-btn-primary" href="/atlas">{AT.b} <span>{ARR}</span></a>
          </div>
        </FadeIn>
      </section>

'''

PLUS = '''        <div style={{marginTop:56, padding:32, border:'1px solid var(--gf-line-strong)', borderRadius:6, display:'flex', flexWrap:'wrap', gap:24, alignItems:'center', justifyContent:'space-between'}}>
          <div style={{flex:'1 1 420px'}}>
            <div className="gf-kicker" style={{color:'var(--gf-warn)'}}>GREENFIELD ATLAS</div>
            <div className="gf-display" style={{fontSize:22, margin:'12px 0 10px'}}>{AT.pt}</div>
            <p style={{color:'var(--gf-fg-dim)', fontSize:14.5, lineHeight:1.6, margin:0}}>{AT.pd}</p>
          </div>
          <a href="/atlas" className="gf-btn gf-btn-ghost" style={{borderColor:'var(--gf-warn)', color:'var(--gf-warn)'}}>{AT.pb} <span>{ARR}</span></a>
        </div>
'''

LI_APP = ('<li><div><strong><a href="/atlas" style="color:inherit" data-en="' + TXT['en']['lt'] + ' →" data-ar="' + TXT['ar']['lt'] + ' ←">'
          + TXT['fr']['lt'] + ' →</a></strong><span data-en="' + TXT['en']['ld'] + '" data-ar="' + TXT['ar']['ld'] + '">' + TXT['fr']['ld'] + '</span></div></li>')


def application(s):
    arr = pour_app("const ARR = window.GF_RTL ? '←' : '→'" + PV + NL)
    s = une_fois(s, arr, arr + pour_app(DEF), 'textes Atlas')
    proc = pour_app('      {/* PROCESSUS */}' + NL)
    s = une_fois(s, proc, pour_app(SECTION) + proc, 'section Atlas')
    fin = pour_app('      </section>' + NL + '    </div>' + NL + '  )' + PV + NL + '}' + NL + NL + 'function StepReveal')
    s = une_fois(s, fin, pour_app(PLUS) + fin, 'Programme Plus')
    liv = pour_app('<ol class="livrables"><li><div><strong data-en="Formal search brief')
    s = une_fois(s, liv, pour_app('<ol class="livrables">' + LI_APP) + pour_app('<li><div><strong data-en="Formal search brief'), 'livrables sourcing')
    return s


app = os.path.join('public', 'app-src.html')
ecrire(app, application(lire(app)))


# 2. Pages statiques
def accueil(s, t):
    a = '</div></div></div></section><section class="block">'
    i = s.find(a)
    assert s.find('class="cards"') < i < s.find('<ol class="livrables">'), 'accueil statique'
    bloc = ('<section class="block"><div class="kicker">Greenfield Atlas</div><div><h2 class="display">' + t['h1'] + '<em>' + t['h2'] + '</em>.</h2>'
            + '<p class="gf-p">' + t['p'] + '</p><p class="gf-p"><a class="btn btn-primary" href="/atlas">' + t['b'] + ' ' + t['fl'] + '</a></p></div></section>')
    j = i + len('</div></div></div></section>')
    return s[:j] + bloc + s[j:]


def sourcing(s, t):
    a = '<ol class="livrables"><li>'
    li = '<li><div><strong><a href="/atlas" style="color:inherit">' + t['lt'] + ' ' + t['fl'] + '</a></strong><span>' + t['ld'] + '</span></div></li>'
    return une_fois(s, a, '<ol class="livrables">' + li + '<li>', 'sourcing statique')


def faq(s, t):
    h = '<h2 class="display">'
    i = s.find(h, s.find(h) + 1)
    a = '<div class="gf-faq">'
    j = s.find(a, i)
    assert 0 < i < j, 'faq statique'
    q = '<details><summary>' + t['fq'] + '</summary><p>' + t['fa1'] + '<a href="/atlas">Greenfield Atlas</a>' + t['fa2'] + '</p></details>'
    j = j + len(a)
    return s[:j] + q + s[j:]


def prix(s, t):
    a = '</p></header>'
    return une_fois(s, a, '</p><p><a class="btn btn-primary" href="/atlas">' + t['px'] + ' ' + t['fl'] + '</a></p></header>', 'prix statique')


PAGES = {'': accueil, 'sourcing-terrain': sourcing, 'faq': faq, 'prix-terrain-casablanca': prix}
faits = {k: 0 for k in PAGES}
for chemin in glob.glob(os.path.join('public', '**', '*.html'), recursive=True):
    rel = os.path.relpath(chemin, 'public').replace(os.sep, '/')
    if rel == 'app-src.html':
        continue
    if rel.startswith('atlas/'):
        continue
    nom = rel[:-len('.html')]
    if nom == 'index':
        nom = ''
    if nom.endswith('/index'):
        nom = nom[:-len('/index')]
    morceaux = [m for m in nom.split('/') if m]
    if morceaux and morceaux[0] in ('en', 'ar'):
        morceaux = morceaux[1:]
    nom = '/'.join(morceaux)
    if nom not in PAGES:
        continue
    s = lire(chemin)
    lang = 'fr'
    for l in LANGUES:
        if '<html lang="' + l + '"' in s:
            lang = l
    ecrire(chemin, PAGES[nom](s, TXT[lang]))
    faits[nom] += 1
for k in faits:
    assert faits[k] == 3, 'page ' + k + ' : ' + str(faits[k])

# 3. llms.txt
ll = os.path.join('public', 'llms.txt')
ligne = NL + '- [Greenfield Atlas](https://greenfield.plus/atlas): carte interactive des terrains disponibles à Casablanca et environs, en accès libre en mode découverte (localisation approximative, prix en fourchette), avec filtres par prix, superficie, secteur et zonage'
titre = NL + NL + '## Questions fréquentes'
ecrire(ll, une_fois(lire(ll), titre, ligne + titre, 'llms'))
print('Mentions Atlas ajoutees : ' + str(faits))
