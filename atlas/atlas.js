// Greenfield Atlas, mode découverte uniquement (site public, sans jeton).
// Données : fonction Supabase atlas_decouverte (voir supabase/atlas-decouverte.sql).
// Nécessite Leaflet (window.L), chargé avant ce fichier.
// Un clic sur un terrain n'ouvre pas de fiche : il affiche l'invitation à prendre rendez-vous sur la carte floutée.
(function () {
'use strict'

const SUPA_URL = 'https://hjscwsybbcjpditudssq.supabase.co'
const SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhqc2N3c3liYmNqcGRpdHVkc3NxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYyNTQ5MjUsImV4cCI6MjA5MTgzMDkyNX0.OccaI1Fw16ldu_PMElJvLyz7b-2EWmmXHeEEyPxeC2w'
const CASABLANCA = [33.56, -7.62]
const ZOOM = 12

const FAM = [
  { k: 'A', l: 'Zone A (immeubles)', col: '#78d6cb' },
  { k: 'B', l: 'Zone B et BT', col: '#7ee0a4' },
  { k: 'C', l: 'Zone C', col: '#c3b2ff' },
  { k: 'D', l: 'Zone D (villas)', col: '#cde88f' },
  { k: 'E', l: 'Zone E', col: '#9fcaff' },
  { k: 'I', l: 'Industriel (I)', col: '#f2b860' },
  { k: 'R', l: 'Rural, agricole (R)', col: '#e2cf9e' },
  { k: 'X', l: 'Autres ou non renseigné', col: '#d3dcd6' }
]
const FAMC = {}
FAM.forEach(f => { FAMC[f.k] = f })
const fam = z => {
  const c = String(z ?? '').trim().charAt(0).toUpperCase()
  return FAMC[c] ? c : 'X'
}

const PRE = {
  p: [['Moins de 10 MDH', null, 10], ['10 à 30 MDH', 10, 30], ['30 à 100 MDH', 30, 100], ['Plus de 100 MDH', 100, null]],
  s: [['Moins de 0,5 ha', null, 0.5], ['0,5 à 2 ha', 0.5, 2], ['2 à 10 ha', 2, 10], ['Plus de 10 ha', 10, null]]
}
const LABEL = { p: 'Prix', s: 'Superficie', q: 'Zones', z: 'Zonage' }

const $ = id => document.getElementById(id)
const root = $('atlas')
const pop = $('atl-pop')
const txt = $('atl-txt')
const esc = s => {
  const d = document.createElement('div')
  d.textContent = String(s ?? '')
  return d.innerHTML.replace(/"/g, '”')
}
const nb = n => String(n).replace('.', ',')
const num = v => {
  const x = parseFloat(String(v).replace(/\s/g, '').replace(',', '.'))
  return isFinite(x) && x >= 0 ? x : null
}
const hasR = r => r[0] != null ? true : r[1] != null
const rangeTxt = (r, u) => {
  if (r[0] != null && r[1] != null) return nb(r[0]) + ' à ' + nb(r[1]) + ' ' + u
  return r[0] != null ? 'Plus de ' + nb(r[0]) + ' ' + u : 'Moins de ' + nb(r[1]) + ' ' + u
}
const norm = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
const numerique = k => k === 'p' ? true : k === 's'

// État des filtres
const F = { p: [null, null], pnd: false, s: [null, null], q: new Set(), z: new Set() }
let D = []
let popK = null

// Carte, centrée sur Casablanca
const map = L.map('atl-map', { zoomControl: false }).setView(CASABLANCA, ZOOM)
L.control.zoom({ position: 'bottomright' }).addTo(map)
const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/'
const sat = L.layerGroup([
  L.tileLayer(esri + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagerie © Esri, Maxar, Earthstar Geographics' }),
  L.tileLayer(esri + 'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, opacity: 0.8 }),
  L.tileLayer(esri + 'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 })
]).addTo(map)
const plan = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 19, attribution: '© OpenStreetMap © CARTO' })
const couche = L.featureGroup().addTo(map)
let fond = 'sat'

$('atl-base').addEventListener('click', () => {
  if (fond === 'sat') {
    map.removeLayer(sat)
    plan.addTo(map)
    fond = 'plan'
  } else {
    map.removeLayer(plan)
    sat.addTo(map)
    fond = 'sat'
  }
  $('atl-base').title = fond === 'sat' ? 'Fond actuel : satellite' : 'Fond actuel : plan'
})

// Invitation à prendre rendez-vous, sur la carte floutée
let retour = null
const ouvrir = () => {
  closePop()
  retour = document.activeElement
  root.classList.add('locked')
  $('atl-cta').focus()
}
const fermer = () => {
  root.classList.remove('locked')
  if (retour && retour.focus) retour.focus()
}
$('atl-modal').addEventListener('click', e => {
  if (e.target === $('atl-modal')) return fermer()
  if (e.target.closest('[data-close]')) fermer()
})
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return
  if (root.classList.contains('locked')) fermer()
  else closePop()
})

// Filtres
const visible = t => {
  const q = norm(txt.value).trim()
  if (q && !norm([t.q, t.z, FAMC[fam(t.z)].l].join(' ')).includes(q)) return false
  if (F.pnd && t.pflo) return false
  if (hasR(F.p)) {
    if (!t.pflo) return false
    if (F.p[0] != null && t.pfhi < F.p[0]) return false
    if (F.p[1] != null && t.pflo > F.p[1]) return false
  }
  if (hasR(F.s)) {
    if (!t.s) return false
    const h = t.s / 10000
    if (F.s[0] != null && h < F.s[0]) return false
    if (F.s[1] != null && h > F.s[1]) return false
  }
  if (F.q.size && !F.q.has(t.q)) return false
  if (F.z.size && !F.z.has(fam(t.z))) return false
  return true
}

const dessiner = t => {
  const col = FAMC[fam(t.z)].col
  if (t.g && t.g.length) {
    L.polygon(t.g, { color: col, weight: 2.5, dashArray: '6 5', fillColor: col, fillOpacity: 0.25 }).on('click', ouvrir).addTo(couche)
  }
  if (t.lat != null && t.lng != null) {
    L.circleMarker([t.lat, t.lng], { radius: 6, color: '#fff', weight: 1.5, fillColor: col, fillOpacity: 1 }).on('click', ouvrir).addTo(couche)
  }
}

const setBtn = (k, on, label) => {
  const b = document.querySelector('.atl-fp[data-p="' + k + '"]')
  b.classList.toggle('on', on)
  b.textContent = label
}

function render () {
  const vus = D.filter(visible)
  couche.clearLayers()
  vus.forEach(dessiner)
  const pOn = F.pnd ? true : hasR(F.p)
  setBtn('p', pOn, F.pnd ? 'Prix sur demande' : (hasR(F.p) ? rangeTxt(F.p, 'MDH') : LABEL.p))
  setBtn('s', hasR(F.s), hasR(F.s) ? rangeTxt(F.s, 'ha') : LABEL.s)
  setBtn('q', F.q.size > 0, F.q.size === 1 ? [...F.q][0] : (F.q.size ? 'Zones (' + F.q.size + ')' : LABEL.q))
  setBtn('z', F.z.size > 0, F.z.size === 1 ? FAMC[[...F.z][0]].l.replace(/ \(.*\)/, '') : (F.z.size ? 'Zonage (' + F.z.size + ')' : LABEL.z))
  const actif = [txt.value.trim() !== '', pOn, hasR(F.s), F.q.size > 0, F.z.size > 0].some(Boolean)
  $('atl-reset').classList.toggle('on', actif)
  const n = vus.length
  const base = n + (n > 1 ? ' terrains' : ' terrain')
  $('atl-n').textContent = actif ? base + ' sur ' + D.length : base + ' en mode découverte'
  $('atl-msg').textContent = D.length && !n ? 'Aucun terrain ne correspond à ces filtres.' : ''
  const see = pop.querySelector('[data-a="see"]')
  if (see) see.textContent = 'Voir ' + base
}

// Menus déroulants de la barre de filtres
function closePop () {
  popK = null
  pop.classList.remove('on')
  document.querySelectorAll('.atl-fp').forEach(b => b.classList.remove('open'))
}

const popBody = k => {
  if (numerique(k)) {
    const r = F[k]
    const u = k === 'p' ? 'MDH' : 'ha'
    const pre = PRE[k].map((x, i) => '<button type="button" data-pre="' + i + '" class="' + (!F.pnd && hasR(r) && r[0] === x[1] && r[1] === x[2] ? 'on' : '') + '">' + x[0] + '</button>').join('') +
      (k === 'p' ? '<button type="button" data-pre="nd" class="' + (F.pnd ? 'on' : '') + '">Sur demande</button>' : '')
    return '<div class="atl-ph">' + (k === 'p' ? 'Prix global' : 'Superficie') + '</div><div class="atl-pre">' + pre + '</div>' +
      '<div class="atl-ph">Ou une fourchette</div><div class="atl-rg">' +
      '<label>Min (' + u + ')<input inputmode="decimal" data-r="0" placeholder="Pas de min" value="' + (r[0] != null ? nb(r[0]) : '') + '"></label>' +
      '<label>Max (' + u + ')<input inputmode="decimal" data-r="1" placeholder="Pas de max" value="' + (r[1] != null ? nb(r[1]) : '') + '"></label></div>'
  }
  if (k === 'q') {
    const n = {}
    D.forEach(t => { if (t.q) n[t.q] = (n[t.q] ?? 0) + 1 })
    const qs = Object.keys(n).sort((a, b) => a.localeCompare(b, 'fr'))
    return '<input type="search" class="atl-pq" placeholder="Chercher une zone" aria-label="Chercher une zone">' +
      '<div class="atl-opts">' + qs.map(q => '<label class="atl-opt" data-t="' + esc(norm(q)) + '"><input type="checkbox" value="' + esc(q) + '"' + (F.q.has(q) ? ' checked' : '') + '><span>' + esc(q) + '</span><small>' + n[q] + '</small></label>').join('') + '</div>'
  }
  const n = {}
  D.forEach(t => { n[fam(t.z)] = (n[fam(t.z)] ?? 0) + 1 })
  return '<div class="atl-ph">Aucun choix : tous les zonages</div><div class="atl-opts">' + FAM.filter(f => n[f.k]).map(f => '<label class="atl-opt"><input type="checkbox" value="' + f.k + '"' + (F.z.has(f.k) ? ' checked' : '') + '><i style="background:' + f.col + '"></i><span>' + f.l + '</span><small>' + n[f.k] + '</small></label>').join('') + '</div>'
}

const wire = k => {
  const body = pop.querySelector('.atl-pb')
  if (numerique(k)) {
    body.querySelectorAll('[data-pre]').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.pre === 'nd') {
        F.pnd = !F.pnd
        F.p = [null, null]
      } else {
        const x = PRE[k][Number(b.dataset.pre)]
        const same = !F.pnd && hasR(F[k]) && F[k][0] === x[1] && F[k][1] === x[2]
        F[k] = same ? [null, null] : [x[1], x[2]]
        if (k === 'p') F.pnd = false
      }
      body.innerHTML = popBody(k)
      wire(k)
      render()
    }))
    body.querySelectorAll('[data-r]').forEach(inp => inp.addEventListener('input', () => {
      const r = [num(body.querySelector('[data-r="0"]').value), num(body.querySelector('[data-r="1"]').value)]
      F[k] = r
      if (k === 'p') F.pnd = false
      body.querySelectorAll('[data-pre]').forEach(b => {
        const x = b.dataset.pre === 'nd' ? null : PRE[k][Number(b.dataset.pre)]
        b.classList.toggle('on', x ? (hasR(r) && r[0] === x[1] && r[1] === x[2]) : false)
      })
      render()
    }))
    return
  }
  const set = F[k]
  body.querySelectorAll('input[type="checkbox"]').forEach(c => c.addEventListener('change', () => {
    if (c.checked) set.add(c.value)
    else set.delete(c.value)
    render()
  }))
  const pq = body.querySelector('.atl-pq')
  if (pq) {
    pq.addEventListener('input', () => {
      const v = norm(pq.value).trim()
      body.querySelectorAll('.atl-opt').forEach(o => { o.style.display = o.dataset.t.includes(v) ? '' : 'none' })
    })
  }
}

const openPop = k => {
  if (popK === k) return closePop()
  popK = k
  document.querySelectorAll('.atl-fp').forEach(b => b.classList.toggle('open', b.dataset.p === k))
  pop.innerHTML = '<div class="atl-pb">' + popBody(k) + '</div><div class="atl-pf"><button type="button" class="btn btn-ghost" data-a="clr">Effacer</button><button type="button" class="btn btn-primary" data-a="see"></button></div>'
  pop.classList.add('on')
  const box = root.getBoundingClientRect()
  const bt = document.querySelector('.atl-fp[data-p="' + k + '"]').getBoundingClientRect()
  const top = bt.bottom - box.top + 8
  pop.style.top = top + 'px'
  pop.style.maxHeight = (box.height - top - 12) + 'px'
  pop.style.left = Math.max(8, Math.min(bt.left - box.left, box.width - pop.offsetWidth - 8)) + 'px'
  wire(k)
  render()
}

document.querySelectorAll('.atl-fp').forEach(b => b.addEventListener('click', () => openPop(b.dataset.p)))
pop.addEventListener('click', e => {
  const a = e.target.closest('[data-a]')
  if (!a) return
  if (a.dataset.a === 'see') return closePop()
  const k = popK
  if (k === 'p') {
    F.p = [null, null]
    F.pnd = false
  } else if (k === 's') F.s = [null, null]
  else F[k].clear()
  pop.querySelector('.atl-pb').innerHTML = popBody(k)
  wire(k)
  render()
})
document.addEventListener('mousedown', e => {
  if (!popK) return
  if (e.target.closest('.atl-pop') ?? e.target.closest('.atl-fp')) return
  closePop()
})
txt.addEventListener('input', render)
$('atl-reset').addEventListener('click', () => {
  txt.value = ''
  F.p = [null, null]
  F.pnd = false
  F.s = [null, null]
  F.q.clear()
  F.z.clear()
  closePop()
  render()
  map.setView(CASABLANCA, ZOOM)
})

// Plein écran
const fsBtn = $('atl-fs')
const fsEl = () => document.fullscreenElement ?? document.webkitFullscreenElement ?? null
fsBtn.addEventListener('click', () => {
  if (fsEl()) {
    if (document.exitFullscreen) document.exitFullscreen()
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen()
  } else if (root.requestFullscreen) root.requestFullscreen()
  else if (root.webkitRequestFullscreen) root.webkitRequestFullscreen()
})
const fsPaint = () => {
  const on = fsEl() === root
  fsBtn.classList.toggle('on', on)
  fsBtn.setAttribute('aria-label', on ? 'Quitter le plein écran' : 'Plein écran')
  fsBtn.title = on ? 'Quitter le plein écran' : 'Plein écran'
  setTimeout(() => map.invalidateSize(), 150)
}
document.addEventListener('fullscreenchange', fsPaint)
document.addEventListener('webkitfullscreenchange', fsPaint)
window.addEventListener('resize', () => { if (popK) closePop() })

// Chargement
fetch(SUPA_URL + '/rest/v1/rpc/atlas_decouverte', {
  method: 'POST',
  headers: { apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY, 'Content-Type': 'application/json' },
  body: '{}'
}).then(r => {
  if (!r.ok) throw new Error('HTTP ' + r.status)
  return r.json()
}).then(terrains => {
  D = terrains
  render()
}).catch(() => {
  $('atl-n').textContent = 'Carte indisponible'
  $('atl-msg').textContent = 'La carte est momentanément indisponible. Réessayez dans quelques instants.'
})
})()
