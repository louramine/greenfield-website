// Greenfield Atlas, mode découverte uniquement (site public, sans jeton).
// Données : fonction Supabase atlas_decouverte (voir supabase/atlas-decouverte.sql).
// Nécessite Leaflet (window.L), chargé avant ce fichier.
(function () {
'use strict'

const SUPA_URL = 'https://hjscwsybbcjpditudssq.supabase.co'
const SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhqc2N3c3liYmNqcGRpdHVkc3NxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYyNTQ5MjUsImV4cCI6MjA5MTgzMDkyNX0.OccaI1Fw16ldu_PMElJvLyz7b-2EWmmXHeEEyPxeC2w'
const CASABLANCA = [33.5731, -7.5898]
const ZOOM_CASABLANCA = 12

const ZONES = {
  A: { l: 'Zone A (immeubles)', c: '#78d6cb' },
  B: { l: 'Zone B et BT', c: '#7ee0a4' },
  C: { l: 'Zone C', c: '#c3b2ff' },
  D: { l: 'Zone D (villas)', c: '#cde88f' },
  E: { l: 'Zone E', c: '#9fcaff' },
  I: { l: 'Industriel (I)', c: '#f2b860' },
  R: { l: 'Rural, agricole (R)', c: '#e2cf9e' },
  X: { l: 'Autres ou non renseigné', c: '#d3dcd6' }
}

const PRIX = [
  { k: 'p1', l: 'Moins de 1 000 MAD le m²' },
  { k: 'p2', l: '1 000 à 3 000 MAD le m²' },
  { k: 'p3', l: '3 000 à 10 000 MAD le m²' },
  { k: 'p4', l: '10 000 MAD le m² et plus' },
  { k: 'pn', l: 'Prix sur demande' }
]
const SURFACE = [
  { k: 's1', l: 'Moins de 1 000 m²' },
  { k: 's2', l: '1 000 m² à 1 ha' },
  { k: 's3', l: '1 ha à 5 ha' },
  { k: 's4', l: '5 ha et plus' },
  { k: 'sn', l: 'Superficie non renseignée' }
]
const LIBELLES = { prix: 'Prix', surface: 'Superficie', zones: 'Zones', zonage: 'Zonage' }

const F = { texte: '', prix: new Set(), surface: new Set(), zones: new Set(), zonage: new Set() }
let TOUS = []
let carte = null
let couche = null
let imagerie = null
let plan = null
let satellite = true
let panneau = null

const $ = s => document.querySelector(s)
const $$ = s => Array.from(document.querySelectorAll(s))
const gf = $('#gf')
const pop = $('#pop')
const liste = $('#liste')
const compte = $('#compte')
const voile = $('#voile')

const esc = s => {
  const d = document.createElement('div')
  d.textContent = String(s ?? '')
  return d.innerHTML
}
const fmt = n => Math.round(n).toLocaleString('fr-FR').replace(/[  ]/g, ' ')
const dec1 = n => String(Math.round(n * 10) / 10).replace('.', ',')
const surfaceTxt = s => (s >= 10000 ? dec1(s / 10000) + ' ha' : fmt(s) + ' m²')
const zone = z => {
  const c = String(z ?? '').trim().charAt(0).toUpperCase()
  return ZONES[c] ? c : 'X'
}
const moyennePrix = t => (t.pmlo && t.pmhi ? (t.pmlo + t.pmhi) / 2 : null)
const clePrix = t => {
  const m = moyennePrix(t)
  if (m === null) return 'pn'
  if (m < 1000) return 'p1'
  if (m < 3000) return 'p2'
  if (m < 10000) return 'p3'
  return 'p4'
}
const cleSurface = t => {
  if (!t.s) return 'sn'
  if (t.s < 1000) return 's1'
  if (t.s < 10000) return 's2'
  if (t.s < 50000) return 's3'
  return 's4'
}
const localisation = t => (t.q ? esc(t.q) : 'Localisation sur demande')
const superficie = t => (t.s ? surfaceTxt(t.s) : 'Superficie sur demande')
const prixTxt = t => {
  const lignes = []
  if (t.pmlo && t.pmhi) lignes.push(fmt(t.pmlo) + ' à ' + fmt(t.pmhi) + ' MAD le m²')
  if (t.pflo && t.pfhi) lignes.push(dec1(t.pflo) + ' à ' + dec1(t.pfhi) + ' MDH')
  return lignes.length ? lignes.join(', ') : 'Prix sur demande'
}

const charger = () => fetch(SUPA_URL + '/rest/v1/rpc/atlas_decouverte', {
  method: 'POST',
  headers: { apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY, 'Content-Type': 'application/json' },
  body: '{}'
}).then(r => {
  if (!r.ok) throw new Error('HTTP ' + r.status)
  return r.json()
})

// Filtres
const passe = t => {
  const q = F.texte.trim().toLowerCase()
  if (q) {
    const texte = ((t.q ?? '') + ' ' + t.id).toLowerCase()
    if (!texte.includes(q)) return false
  }
  if (F.prix.size && !F.prix.has(clePrix(t))) return false
  if (F.surface.size && !F.surface.has(cleSurface(t))) return false
  if (F.zones.size && !F.zones.has(t.q ?? '')) return false
  if (F.zonage.size && !F.zonage.has(zone(t.z))) return false
  return true
}
const quartiers = () => {
  const m = new Map()
  TOUS.forEach(t => { if (t.q) m.set(t.q, (m.get(t.q) ?? 0) + 1) })
  return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0], 'fr'))
}
const ensembles = () => ({ prix: F.prix, surface: F.surface, zones: F.zones, zonage: F.zonage })

// Carte
const dessiner = t => {
  const z = ZONES[zone(t.z)]
  const clic = () => ouvrirModale()
  if (t.g && t.g.length) {
    L.polygon(t.g, { color: z.c, weight: 2, dashArray: '6 5', fillColor: z.c, fillOpacity: 0.25 }).on('click', clic).addTo(couche)
  } else if (t.lat != null && t.lng != null) {
    L.circleMarker([t.lat, t.lng], { radius: 6, color: '#fff', weight: 1.5, fillColor: z.c, fillOpacity: 1 }).on('click', clic).addTo(couche)
  }
}

const ligneListe = t => '<button type="button" class="carte-t" data-id="' + esc(t.id) + '">' +
  '<span class="id">' + esc(t.id) + '</span>' +
  '<span class="lieu">' + localisation(t) + '</span>' +
  '<span class="plaque" style="background:' + ZONES[zone(t.z)].c + '">Zone ' + zone(t.z) + '</span>' +
  '<span class="surf">' + superficie(t) + '</span>' +
  '<span class="prix">' + esc(prixTxt(t)) + '</span>' +
  '</button>'

const majBoutons = () => {
  $$('.fp').forEach(b => {
    const p = b.dataset.p
    const n = ensembles()[p].size
    b.textContent = LIBELLES[p] + (n ? ' (' + n + ')' : '')
    b.classList.toggle('actif', n > 0)
  })
}

const rafraichir = () => {
  const ok = TOUS.filter(passe)
  couche.clearLayers()
  ok.forEach(dessiner)
  liste.innerHTML = ok.length ? ok.map(ligneListe).join('') : '<p class="vide">Aucun terrain ne correspond à ces critères.</p>'
  const n = ok.length
  compte.textContent = n === 0 ? 'Aucun terrain pour ces critères' : (n > 1 ? n + ' terrains disponibles' : n + ' terrain disponible') + ' en découverte'
  majBoutons()
}

// Panneaux de filtres
const ligne = (groupe, valeur, html, coche) => '<label class="ligne"><input type="checkbox" data-g="' + groupe + '" data-v="' + encodeURIComponent(valeur) + '"' + (coche ? ' checked' : '') + '><span>' + html + '</span></label>'

const contenuPanneau = p => {
  if (p === 'zones') {
    const items = quartiers().map(([nom, n]) => ligne('zones', nom, esc(nom) + ' <em>' + n + '</em>', F.zones.has(nom))).join('')
    return '<h3>Zones</h3><input type="search" id="filtre-zones" placeholder="Chercher une zone" aria-label="Chercher une zone"><div class="items">' + items + '</div>'
  }
  if (p === 'zonage') {
    const items = Object.keys(ZONES).map(k => ligne('zonage', k, '<i class="pastille" style="background:' + ZONES[k].c + '"></i>' + esc(ZONES[k].l), F.zonage.has(k))).join('')
    return '<h3>Zonage</h3>' + items
  }
  if (p === 'prix') {
    return '<h3>Prix au m²</h3>' + PRIX.map(x => ligne('prix', x.k, esc(x.l), F.prix.has(x.k))).join('')
  }
  return '<h3>Superficie</h3>' + SURFACE.map(x => ligne('surface', x.k, esc(x.l), F.surface.has(x.k))).join('')
}

const fermerPanneau = () => {
  panneau = null
  pop.hidden = true
  $$('.fp').forEach(b => b.setAttribute('aria-expanded', 'false'))
}

const ouvrirPanneau = (p, bouton) => {
  if (panneau === p) return fermerPanneau()
  panneau = p
  pop.innerHTML = contenuPanneau(p)
  const decalage = bouton.getBoundingClientRect().left - gf.getBoundingClientRect().left
  pop.style.left = Math.max(12, decalage) + 'px'
  pop.hidden = false
  $$('.fp').forEach(b => b.setAttribute('aria-expanded', b === bouton ? 'true' : 'false'))
  const recherche = pop.querySelector('#filtre-zones')
  if (recherche) {
    recherche.addEventListener('input', () => {
      const q = recherche.value.trim().toLowerCase()
      pop.querySelectorAll('.items .ligne').forEach(l => { l.hidden = !l.textContent.toLowerCase().includes(q) })
    })
  }
}

// Fiche modale
const ouvrirModale = () => {
  voile.hidden = false
  $('#fermer').focus()
}
const fermerModale = () => {
  voile.hidden = true
}

// Vues et fond de carte
const setVue = mode => {
  gf.dataset.vue = mode
  $$('.vue button').forEach(b => b.classList.toggle('actif', b.dataset.mode === mode))
  setTimeout(() => carte.invalidateSize(), 60)
}

const basculerFond = () => {
  if (satellite) {
    carte.removeLayer(imagerie)
    carte.addLayer(plan)
    $('#fond').textContent = 'Satellite'
  } else {
    carte.removeLayer(plan)
    carte.addLayer(imagerie)
    $('#fond').textContent = 'Plan'
  }
  satellite = !satellite
}

const reinitialiser = () => {
  F.texte = ''
  F.prix.clear()
  F.surface.clear()
  F.zones.clear()
  F.zonage.clear()
  $('#recherche').value = ''
  fermerPanneau()
  carte.setView(CASABLANCA, ZOOM_CASABLANCA)
  rafraichir()
}

const lier = () => {
  $('#recherche').addEventListener('input', e => {
    F.texte = e.target.value
    rafraichir()
  })
  $$('.fp').forEach(b => b.addEventListener('click', e => {
    e.stopPropagation()
    ouvrirPanneau(b.dataset.p, b)
  }))
  pop.addEventListener('change', e => {
    const t = e.target
    if (!t.dataset.g) return
    const v = decodeURIComponent(t.dataset.v)
    const ens = ensembles()[t.dataset.g]
    if (t.checked) ens.add(v)
    else ens.delete(v)
    rafraichir()
  })
  pop.addEventListener('click', e => e.stopPropagation())
  document.addEventListener('click', () => { if (panneau) fermerPanneau() })
  $('#reinit').addEventListener('click', reinitialiser)
  $$('.vue button').forEach(b => b.addEventListener('click', () => setVue(b.dataset.mode)))
  $('#plein').addEventListener('click', () => {
    if (document.fullscreenElement) document.exitFullscreen()
    else if (gf.requestFullscreen) gf.requestFullscreen()
  })
  document.addEventListener('fullscreenchange', () => setTimeout(() => carte.invalidateSize(), 150))
  $('#fond').addEventListener('click', basculerFond)
  liste.addEventListener('click', e => {
    if (e.target.closest('.carte-t')) ouvrirModale()
  })
  voile.addEventListener('click', e => { if (e.target === voile) fermerModale() })
  $('#fermer').addEventListener('click', fermerModale)
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      fermerModale()
      fermerPanneau()
    }
  })
}

const init = () => {
  const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/'
  carte = L.map('carte', { zoomControl: false }).setView(CASABLANCA, ZOOM_CASABLANCA)
  L.control.zoom({ position: 'bottomright' }).addTo(carte)
  imagerie = L.layerGroup([
    L.tileLayer(esri + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagerie © Esri, Maxar, Earthstar Geographics' }),
    L.tileLayer(esri + 'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, opacity: 0.8 }),
    L.tileLayer(esri + 'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 })
  ])
  plan = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 19, attribution: '© OpenStreetMap © CARTO' })
  imagerie.addTo(carte)
  couche = L.featureGroup().addTo(carte)
  lier()
  charger().then(donnees => {
    TOUS = donnees
    rafraichir()
  }).catch(() => {
    compte.textContent = 'La carte est momentanément indisponible. Réessayez dans quelques instants.'
  })
}

init()
})()
