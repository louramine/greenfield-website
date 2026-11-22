# Branche le formulaire de contact de l'accueil sur Supabase (fonction soumettre_demande).
# Avant : le bouton affichait « Brief transmis » sans rien envoyer.
# Ajoute la validation des champs, un champ piege anti-robots, un message d'erreur et l'envoi reel.
# Le build echoue si un emplacement attendu est introuvable : la production reste alors inchangee.
import io
import json
import os

PV = chr(59)

SUPA = 'https://hjscwsybbcjpditudssq.supabase.co'
CLE = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhqc2N3c3liYmNqcGRpdHVkc3NxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYyNTQ5MjUsImV4cCI6MjA5MTgzMDkyNX0'
       '.OccaI1Fw16ldu_PMElJvLyz7b-2EWmmXHeEEyPxeC2w')


def lire(chemin):
    return io.open(chemin, encoding='utf-8').read()


def ecrire(chemin, texte):
    io.open(chemin, 'w', encoding='utf-8').write(texte)


def esc(code):
    # Le code de l'accueil est stocke dans une chaine JSON (modele du bundler)
    s = json.dumps(code, ensure_ascii=False)[1:-1]
    return s.replace('</', '<' + chr(92) + 'u002F')


def une_fois(s, ancien, nouveau, nom):
    a = esc(ancien)
    n = s.count(a)
    assert n == 1, nom + ' : ' + str(n) + ' occurrence(s)'
    return s.replace(a, esc(nouveau))


AIDE = '''const GF_SUPA = '__SUPA__'
const GF_KEY = '__CLE__'
const GF_T0 = Date.now()
const gfLangue = () => {
  const l = window.GF_LANG ? window.GF_LANG : document.documentElement.lang
  return l === 'ar' ? 'ar' : (l === 'en' ? 'en' : 'fr')
}
const GF_MOTS = {
  fr: { nom: 'Indiquez votre nom.', contact: 'Indiquez un email ou un numéro de téléphone.', email: 'Cet email ne semble pas valide.', telephone: 'Ce numéro de téléphone ne semble pas valide.', limite: 'Trop d’envois depuis cet appareil. Réessayez plus tard ou écrivez-nous sur WhatsApp.', reseau: 'L’envoi a échoué. Réessayez ou écrivez-nous sur WhatsApp au +212 7 76 25 00 52.', envoi: 'Envoi en cours…' },
  en: { nom: 'Please enter your name.', contact: 'Please enter an email or a phone number.', email: 'This email does not look valid.', telephone: 'This phone number does not look valid.', limite: 'Too many messages from this device. Please try again later or contact us on WhatsApp.', reseau: 'Sending failed. Please try again or contact us on WhatsApp at +212 7 76 25 00 52.', envoi: 'Sending…' },
  ar: { nom: 'يرجى إدخال اسمكم.', contact: 'يرجى إدخال بريد إلكتروني أو رقم هاتف.', email: 'البريد الإلكتروني غير صالح.', telephone: 'رقم الهاتف غير صالح.', limite: 'عدد كبير من الرسائل من هذا الجهاز. يرجى المحاولة لاحقًا أو مراسلتنا عبر واتساب.', reseau: 'تعذر الإرسال. يرجى المحاولة مجددًا أو مراسلتنا عبر واتساب على 0052 25 76 7 212+.', envoi: 'جارٍ الإرسال…' }
}
const gfEnvoyer = (f, piege, setBusy, setErr, setSent) => {
  const M = GF_MOTS[gfLangue()]
  const nom = f.name.trim()
  const mail = f.email.trim()
  const tel = f.phone.trim()
  const chiffres = tel.replace(/\\D/g, '').length
  if (nom.length < 2) return setErr(M.nom)
  if (!mail && !tel) return setErr(M.contact)
  if (mail && !/^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$/i.test(mail)) return setErr(M.email)
  if (tel && (chiffres < 8 ? true : chiffres > 15)) return setErr(M.telephone)
  setErr('')
  setBusy(true)
  const p = { nom, societe: f.company, email: mail, telephone: tel, type: f.type, message: f.message, site_web: piege, duree: Math.round((Date.now() - GF_T0) / 1000), langue: gfLangue(), page: location.pathname }
  fetch(GF_SUPA + '/rest/v1/rpc/soumettre_demande', {
    method: 'POST',
    headers: { apikey: GF_KEY, Authorization: 'Bearer ' + GF_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ p })
  })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(d => {
      setBusy(false)
      if (d && d.ok) return setSent(true)
      setErr(d && M[d.erreur] ? M[d.erreur] : M.reseau)
    })
    .catch(() => {
      setBusy(false)
      setErr(M.reseau)
    })
}

function InquiryForm({ variant }) {'''.replace('__SUPA__', SUPA).replace('__CLE__', CLE)

PIEGE = '''{err ? <div role='alert' style={{gridColumn:'span 2', padding:'16px 24px', fontSize:14, fontWeight:600, borderBottom:`1px solid ${fieldBorder}`}}>{err}</div> : null}
            <input type='text' name='site_web' tabIndex={-1} autoComplete='off' aria-hidden='true' value={piege} onChange={e=>setPiege(e.target.value)}
              style={{position:'absolute', left:'-9999px', width:1, height:1, opacity:0}}/>
            <button type="submit" disabled={busy} style={{'''

app = os.path.join('public', 'app-src.html')
s = lire(app)
s = une_fois(s, 'function InquiryForm({ variant }) {', AIDE, 'debut du formulaire')
s = une_fois(s, "type:'Acquisition', message:''", "type:'Achat', message:''", 'type par defaut')
s = une_fois(s, 'const [sent, setSent] = React.useState(false)' + PV,
             "const [sent, setSent] = React.useState(false)" + PV + "\n  const [busy, setBusy] = React.useState(false)\n  const [err, setErr] = React.useState('')\n  const [piege, setPiege] = React.useState('')",
             'etats')
s = une_fois(s, '<form onSubmit={e=>{e.preventDefault()' + PV + ' setSent(true)' + PV + '}}',
             '<form noValidate onSubmit={e=>{e.preventDefault()\n            gfEnvoyer(f, piege, setBusy, setErr, setSent)}}',
             'envoi')
s = une_fois(s, '<input type={t} value={f[k]}', "<input type={t} name={k} required={k==='name'} value={f[k]}", 'champs')
s = une_fois(s, '<button type="submit" style={{', PIEGE, 'bouton')
s = une_fois(s, "cursor:'pointer', textTransform:'uppercase', display:'flex', justifyContent:'space-between',",
             "cursor: busy ? 'wait' : 'pointer', opacity: busy ? 0.7 : 1, textTransform:'uppercase', display:'flex', justifyContent:'space-between',",
             'style du bouton')
s = une_fois(s, "<span>{T('Transmettre le brief')}</span>",
             "<span>{busy ? GF_MOTS[gfLangue()].envoi : T('Transmettre le brief')}</span>", 'texte du bouton')
MENTION = ("</form>\n          <p style={{fontSize:12.5, lineHeight:1.5, opacity:0.75, marginTop:14}}>"
           "{({fr:'Vos informations servent uniquement à vous recontacter au sujet de votre demande.', "
           "en:'Your details are only used to get back to you about your request.', "
           "ar:'تُستعمل معلوماتكم فقط للتواصل معكم بخصوص طلبكم.'})[gfLangue()]} "
           "<a href='/politique-de-confidentialite' style={{color:'inherit'}}>"
           "{({fr:'Politique de confidentialité', en:'Privacy policy', ar:'سياسة الخصوصية'})[gfLangue()]}</a></p>")
s = une_fois(s, '</form>', MENTION, 'mention sous le formulaire')
ecrire(app, s)
print('Formulaire de contact branche sur Supabase')
