# Ajoute au site : politique de confidentialite, mentions legales et conditions d'utilisation, page 404,
# et les liens vers ces pages dans le pied de page de toutes les pages et de l'accueil.
# A lancer apres formulaire_contact.py (l'accueil utilise sa fonction gfLangue).
# Le build echoue si un emplacement attendu est introuvable : la production reste alors inchangee.
import glob
import io
import json
import os

MAJ = '22 novembre 2026'

# Informations de la societe. Un champ qui vaut None n'est pas publie.
SOCIETE = {
    'raison': None,
    'forme': None,
    'capital': None,
    'rc': None,
    'ice': None,
    'if': None,
    'directeur': None,
}


def champ(cle, libelle):
    v = SOCIETE[cle]
    return v if v else '<mark class="gf-todo">[à compléter : ' + libelle + ']</mark>'


def lire(chemin):
    return io.open(chemin, encoding='utf-8').read()


def ecrire(chemin, texte):
    io.open(chemin, 'w', encoding='utf-8').write(texte)


def entre(s, debut, fin):
    i = s.find(debut)
    assert i >= 0, debut
    j = s.find(fin, i)
    assert j >= 0, fin
    return i, j


def couper(s, debut, fin, garder_fin=True):
    i, j = entre(s, debut, fin)
    return s[:i] + s[j + (0 if garder_fin else len(fin)):]


def remplacer_attr(s, avant, nouveau):
    # remplace la valeur entre avant et le guillemet suivant
    i = s.find(avant)
    assert i >= 0, avant
    i += len(avant)
    j = s.find('"', i)
    return s[:i] + nouveau + s[j:]


def section(kicker, titre, corps):
    return ('<section class="block"><div class="kicker">' + kicker + '</div><div><h2 class="display">' + titre +
            '</h2>' + corps + '</div></section>')


def p(texte):
    return '<p class="gf-p">' + texte + '</p>'


def liste(items):
    return '<ul class="gf-p gf-legal-list">' + ''.join('<li>' + x + '</li>' for x in items) + '</ul>'


STYLE = ('<style>.gf-todo{background:#f2b860}.gf-todo{color:#0a1410}.gf-todo{padding:0 4px}.gf-todo{border-radius:3px}'
         '.gf-legal-list{padding-inline-start:1.2em}.gf-legal-list li{margin:0 0 8px}'
         '.gf-404 a{margin:0 16px 12px 0}</style>')

ADRESSE = 'Casa Finance City, Casablanca, Maroc'
CONTACT = ('<a href="mailto:contact@greenfield.plus">contact@greenfield.plus</a> ou par téléphone et WhatsApp au '
           '<a href="tel:+212776250052" dir="ltr">+212 7 76 25 00 52</a>')


def nom_societe():
    return SOCIETE['raison'] + ', exerçant sous le nom Greenfield+' if SOCIETE['raison'] else 'Greenfield+'


def lignes_editeur():
    # Seuls les champs renseignes dans SOCIETE sont publies
    v = SOCIETE
    l = ['Nom : ' + nom_societe()]
    if v['forme']:
        l.append('Forme juridique : ' + v['forme'] + (', au capital de ' + v['capital'] if v['capital'] else ''))
    l.append('Siège : ' + ADRESSE)
    if v['rc']:
        l.append('Registre de commerce : ' + v['rc'])
    if v['ice']:
        l.append('ICE : ' + v['ice'] + (' et identifiant fiscal : ' + v['if'] if v['if'] else ''))
    if v['directeur']:
        l.append('Directeur de la publication : ' + v['directeur'])
    l.append('Contact : ' + CONTACT)
    return l


def confidentialite():
    hero = ('<header class="hero"><div class="kicker">Informations légales</div><h1 class="display">Politique de<br><em>confidentialité</em>.</h1>'
            '<p>Cette page explique quelles données personnelles Greenfield+ recueille sur greenfield.plus, pourquoi, '
            'combien de temps elles sont gardées et comment exercer vos droits, conformément à la loi n° 09-08 relative à la '
            'protection des personnes physiques à l’égard du traitement des données à caractère personnel.</p>'
            '<p class="gf-note">Dernière mise à jour : ' + MAJ + '.</p></header>')
    s = [
        section('Responsable', 'Qui traite vos données',
                p('Le responsable du traitement est ' + nom_societe() + ', ' +
                  ADRESSE + '. Vous pouvez nous joindre à ' + CONTACT + '.')),
        section('Données', 'Les données recueillies',
                liste([
                    '<strong>Formulaire de contact</strong> : nom et prénom, société, email, téléphone, type de recherche et le brief que vous rédigez.',
                    '<strong>Échanges directs</strong> : les informations que vous nous transmettez par téléphone, WhatsApp ou email.',
                    '<strong>Données techniques</strong> : lors d’un envoi du formulaire, votre adresse IP est transformée en une empreinte non réversible, utilisée uniquement pour bloquer les envois abusifs.',
                    '<strong>Carte Atlas et autres pages</strong> : aucune donnée personnelle n’est demandée. Le site garde seulement la langue choisie dans votre navigateur.',
                ])),
        section('Finalités', 'Pourquoi nous les utilisons',
                liste([
                    'Répondre à votre demande et vous recontacter.',
                    'Vous présenter des terrains ou des services correspondant à votre recherche.',
                    'Suivre la relation commerciale avec nos clients et partenaires.',
                    'Protéger le site contre le spam et les envois abusifs.',
                ]) +
                p('Ces traitements reposent sur votre consentement, donné en envoyant le formulaire ou en nous contactant, et sur les '
                  'mesures nécessaires à la préparation d’une mission. Vos données ne sont jamais vendues ni louées.')),
        section('Destinataires', 'Qui y a accès',
                p('Seuls les membres habilités de l’équipe Greenfield+ ont accès à vos données. Elles sont hébergées chez des '
                  'prestataires techniques qui agissent pour notre compte : Supabase (base de données) et Vercel (hébergement du site). '
                  'Leurs serveurs peuvent être situés hors du Maroc. Ces transferts sont réalisés dans le respect des conditions '
                  'prévues par la loi n° 09-08.') +
                p('Pour afficher le site et la carte, votre navigateur charge aussi des polices de caractères (Google Fonts) et des '
                  'fonds de carte (Esri, CARTO, OpenStreetMap). Ces services reçoivent votre adresse IP comme pour toute page web.')),
        section('Durée', 'Combien de temps nous les gardons',
                liste([
                    'Demande restée sans suite : 3 ans à compter du dernier échange.',
                    'Client ou partenaire : pendant toute la relation, puis le temps imposé par nos obligations légales et comptables.',
                    'Empreinte technique anti-abus : 12 mois au plus.',
                ])),
        section('Vos droits', 'Accès, rectification, opposition',
                p('Vous pouvez à tout moment accéder à vos données, les faire corriger ou vous opposer à leur utilisation, '
                  'y compris à des fins de prospection. Écrivez-nous à ' + CONTACT + '. Nous répondons dans un délai d’un mois.') +
                p('Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir la CNDP : '
                  '<a href="https://www.cndp.ma" rel="noopener">www.cndp.ma</a>.')),
        section('Cookies', 'Cookies et mesure d’audience',
                p('Greenfield+ n’utilise aucun cookie publicitaire ni outil de mesure d’audience. Le site enregistre seulement la '
                  'langue que vous choisissez, dans le stockage local de votre navigateur, pour vous afficher la bonne version. '
                  'Si un outil de mesure d’audience est ajouté, un bandeau vous demandera votre accord avant tout dépôt.')),
    ]
    return hero + ''.join(s)


def mentions():
    hero = ('<header class="hero"><div class="kicker">Informations légales</div><h1 class="display">Mentions légales<br>et <em>conditions</em><br>d’utilisation.</h1>'
            '<p>En utilisant greenfield.plus, vous acceptez les conditions ci-dessous.</p>'
            '<p class="gf-note">Dernière mise à jour : ' + MAJ + '.</p></header>')
    s = [
        section('Éditeur', 'Éditeur du site',
                liste(lignes_editeur())),
        section('Hébergement', 'Hébergement',
                p('Le site est hébergé par Vercel Inc., États-Unis (<a href="https://vercel.com" rel="noopener">vercel.com</a>). '
                  'Les données de la carte Atlas et des demandes de contact sont hébergées par Supabase Inc. '
                  '(<a href="https://supabase.com" rel="noopener">supabase.com</a>).')),
        section('Objet', 'Objet du site',
                p('greenfield.plus présente les services de Greenfield+ : sourcing de terrains, vérification juridique et urbanistique, '
                  'études de marché et accompagnement des propriétaires qui souhaitent vendre leur terrain à un promoteur.')),
        section('Informations', 'Des informations indicatives',
                p('Les prix, superficies, zonages et localisations publiés sur le site, sur la carte Atlas et dans le baromètre des prix '
                  'sont donnés à titre indicatif. Sur la carte Atlas, les localisations sont volontairement approximatives et les prix '
                  'présentés en fourchette. Ces informations ne constituent ni une offre ferme de vente, ni un conseil juridique, fiscal '
                  'ou en investissement. Elles doivent être vérifiées, notamment auprès de la Conservation foncière et de l’agence '
                  'urbaine, avant toute décision. Greenfield+ ne saurait être tenue responsable d’une décision prise sur leur seule base.')),
        section('Propriété', 'Propriété intellectuelle',
                p('La marque Greenfield+, le logo, les textes, la carte Atlas, les données et le baromètre des prix sont la propriété de '
                  'Greenfield+. Toute reproduction ou extraction, totale ou partielle, notamment l’extraction automatisée des données de '
                  'la carte, est interdite sans accord écrit préalable. Les logos des clients cités restent la propriété de leurs titulaires.')),
        section('Utilisation', 'Bonne utilisation du site',
                p('Vous vous engagez à transmettre des informations exactes dans le formulaire de contact et à ne pas utiliser le site '
                  'de manière abusive, par exemple par des envois automatisés ou des tentatives d’accès non autorisé.') +
                p('Le site peut contenir des liens vers d’autres sites (LinkedIn, Instagram, WhatsApp). Greenfield+ n’est pas '
                  'responsable de leur contenu.')),
        section('Données', 'Données personnelles',
                p('L’utilisation de vos données personnelles est décrite dans la '
                  '<a href="/politique-de-confidentialite">politique de confidentialité</a>.')),
        section('Droit', 'Droit applicable',
                p('Ces conditions sont régies par le droit marocain. En cas de litige, et à défaut d’accord amiable, '
                  'les tribunaux de Casablanca sont seuls compétents.')),
    ]
    return hero + ''.join(s)


def page404():
    return ('<header class="hero gf-404"><div class="kicker">Erreur 404</div><h1 class="display">Page<br><em>introuvable</em>.</h1>'
            '<p>Cette page n’existe pas ou a été déplacée.</p>'
            '<p lang="en" dir="ltr">This page does not exist or has been moved.</p>'
            '<p lang="ar" dir="rtl">هذه الصفحة غير موجودة أو تم نقلها.</p>'
            '<div class="hero-actions"><a class="btn btn-primary" href="/">Retour à l’accueil →</a>'
            '<a class="btn btn-ghost" href="/atlas">Carte Atlas</a>'
            '<a class="btn btn-ghost" href="/#contact">Prendre contact</a></div></header>')


def construire(modele, titre, description, chemin_url, corps, index=True):
    s = modele
    i, j = entre(s, '<title>', '</title>')
    s = s[:i] + '<title>' + titre + s[j:]
    s = remplacer_attr(s, '<meta name="description" content="', description)
    s = remplacer_attr(s, '<meta property="og:title" content="', titre)
    s = remplacer_attr(s, '<meta property="og:description" content="', description)
    url = 'https://greenfield.plus' + chemin_url
    s = remplacer_attr(s, '<link rel="canonical" href="', url)
    s = remplacer_attr(s, '<meta property="og:url" content="', url)
    while '<link rel="alternate" hreflang=' in s:
        s = couper(s, '<link rel="alternate" hreflang=', '>', garder_fin=False)
    s = couper(s, '<script type="application/ld+json">', '</script>', garder_fin=False)
    if not index:
        s = remplacer_attr(s, '<meta name="robots" content="', 'noindex, follow')
    s = s.replace('</head>', STYLE + '</head>', 1)
    s = couper(s, '<div class="gf-lang">', '</div>', garder_fin=False)
    s = s.replace(' aria-current="page"', '')
    i, j = entre(s, '<header class="hero">', '<div class="gf-links">')
    s = s[:i] + corps + s[j:]
    if '<time datetime="' in s:
        i, j = entre(s, '<time datetime="', '</time>')
        s = s[:i] + '<time datetime="2026-11-22">' + MAJ + s[j:]
    return s


modele = lire(os.path.join('public', 'vendre-mon-terrain.html'))
assert '<html lang="fr"' in modele
pages = {
    'politique-de-confidentialite.html': construire(
        modele, 'Politique de confidentialité · Greenfield+',
        'Données personnelles recueillies par Greenfield+ sur greenfield.plus, finalités, durée de conservation et droits (loi 09-08).',
        '/politique-de-confidentialite', confidentialite()),
    'mentions-legales.html': construire(
        modele, 'Mentions légales et conditions d’utilisation · Greenfield+',
        'Éditeur, hébergement, conditions d’utilisation et propriété intellectuelle du site greenfield.plus.',
        '/mentions-legales', mentions()),
    '404.html': construire(
        modele, 'Page introuvable · Greenfield+', 'Cette page n’existe pas ou a été déplacée.', '/404', page404(), index=False),
}
for nom, html in pages.items():
    ecrire(os.path.join('public', nom), html)

LIBELLES = {
    'fr': ('Mentions légales', 'Confidentialité'),
    'en': ('Legal notice', 'Privacy'),
    'ar': ('إشعار قانوني', 'الخصوصية'),
}


def langue(s):
    for code in ('en', 'ar'):
        if '<html lang="' + code + '"' in s:
            return code
    return 'fr'


n = 0
for chemin in glob.glob(os.path.join('public', '**', '*.html'), recursive=True):
    if os.sep + 'atlas' + os.sep in chemin:
        continue
    if os.path.basename(chemin) == 'app-src.html':
        continue
    s = lire(chemin)
    if '<div class="gf-links-nav">' not in s:
        continue
    m, c = LIBELLES[langue(s)]
    liens = '<a href="/mentions-legales">' + m + '</a><a href="/politique-de-confidentialite">' + c + '</a>'
    i = s.find('<div class="gf-links-nav">')
    j = s.find('</div>', i)
    s = s[:j] + liens + s[j:]
    ecrire(chemin, s)
    n += 1
assert n >= 10, 'pages avec liens legaux : ' + str(n)

# Accueil : liens dans le pied de page (code stocke dans une chaine JSON)
app = os.path.join('public', 'app-src.html')
s = lire(app)
assert 'const gfLangue' in s, 'formulaire_contact.py doit etre lance avant'
ancien = '<div>{T("© 2026 GREENFIELD+ · TERRAINS POUR PROMOTEURS · GREENFIELD.PLUS")}</div>'
lien = "style={{color:'inherit', textDecoration:'none'}}"
nouveau = (ancien + '\n        <div style={{display:\'flex\', gap:20, flexWrap:\'wrap\'}}>'
           '<a href=\'/mentions-legales\' ' + lien + '>{({fr:\'Mentions légales\', en:\'Legal notice\', ar:\'إشعار قانوني\'})[gfLangue()]}</a>'
           '<a href=\'/politique-de-confidentialite\' ' + lien + '>{({fr:\'Confidentialité\', en:\'Privacy\', ar:\'الخصوصية\'})[gfLangue()]}</a></div>')


def esc(code):
    return json.dumps(code, ensure_ascii=False)[1:-1].replace('</', '<' + chr(92) + 'u002F')


a = esc(ancien)
assert s.count(a) == 1, 'pied de page accueil : ' + str(s.count(a))
s = s.replace(a, esc(nouveau))
ecrire(app, s)
print('Pages legales et 404 ajoutees, liens dans ' + str(n) + ' pages et sur l accueil')
