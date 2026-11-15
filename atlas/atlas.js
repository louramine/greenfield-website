// Greenfield Atlas, mode découverte uniquement (site public, sans jeton).
// Données : fonction Supabase atlas_decouverte (voir supabase/atlas-decouverte.sql).
// Nécessite Leaflet (window.L), chargé avant ce fichier.
(function () {
'use strict'

const SUPA_URL = 'https://hjscwsybbcjpditudssq.supabase.co'
const SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhqc2N3c3liYmNqcGRpdHVkc3NxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYyNTQ5MjUsImV4cCI6MjA5MTgzMDkyNX0.OccaI1Fw16ldu_PMElJvLyz7b-2EWmmXHeEEyPxeC2w'
const CENTRE = [33.5731, -7.5898]
const ZOOM = 10

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

const esc = s => {
  const d = document.createElement('div')
  d.textContent = String(s ?? '')
  return d.innerHTML
}
const fmt = n => Math.round(n).toLocaleString('fr-FR').replace(/[  ]/g, ' ')
const dec1 = n => String(Math.round(n * 10) / 10).replace('.', ',')
const surface = s => (s >= 10000 ? dec1(s / 10000) + ' ha' : fmt(s) + ' m²')

const zone = z => {
  const c = String(z ?? '').trim().charAt(0).toUpperCase()
  return ZONES[c] ? c : 'X'
}

const prix = t => {
  const lignes = []
  if (t.pmlo && t.pmhi) lignes.push(fmt(t.pmlo) + ' à ' + fmt(t.pmhi) + ' MAD le m²')
  if (t.pflo && t.pfhi) lignes.push(dec1(t.pflo) + ' à ' + dec1(t.pfhi) + ' MDH')
  return lignes.length ? lignes.join(', ') : 'Prix sur demande'
}

const localisation = t => (t.q ? esc(t.q) : 'Localisation sur demande')
const superficie = t => (t.s ? surface(t.s) : 'Superficie sur demande')

const charger = () => fetch(SUPA_URL + '/rest/v1/rpc/atlas_decouverte', {
  method: 'POST',
  headers: { apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY, 'Content-Type': 'application/json' },
  body: '{}'
}).then(r => {
  if (!r.ok) throw new Error('HTTP ' + r.status)
  return r.json()
})

const dessiner = (t, couche) => {
  const z = ZONES[zone(t.z)]
  const bulle = '<div class="pop"><strong>' + esc(t.id) + '</strong><br>' + localisation(t) + '<br>' + esc(z.l) + '<br>' + superficie(t) + '<br>' + esc(prix(t)) + '<br><em>Forme et localisation approximatives</em></div>'
  if (t.g && t.g.length) {
    L.polygon(t.g, { color: z.c, weight: 2, dashArray: '6 5', fillColor: z.c, fillOpacity: 0.25 }).bindPopup(bulle).addTo(couche)
  } else if (t.lat != null && t.lng != null) {
    L.circleMarker([t.lat, t.lng], { radius: 6, color: '#fff', weight: 1.5, fillColor: z.c, fillOpacity: 1 }).bindPopup(bulle).addTo(couche)
  }
}

const ligne = t => '<li><strong>' + esc(t.id) + '</strong>, ' + localisation(t) + '<br>' + esc(ZONES[zone(t.z)].l) + ' · ' + superficie(t) + '<br>' + esc(prix(t)) + '</li>'

const init = () => {
  const compte = document.getElementById('atlas-compte')
  const liste = document.getElementById('atlas-liste')
  const carte = L.map('atlas-map', { scrollWheelZoom: false }).setView(CENTRE, ZOOM)
  const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/'
  L.tileLayer(esri + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagerie © Esri, Maxar, Earthstar Geographics' }).addTo(carte)
  L.tileLayer(esri + 'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }).addTo(carte)
  const couche = L.featureGroup().addTo(carte)

  charger().then(terrains => {
    const n = terrains.length
    compte.textContent = (n > 1 ? n + ' terrains disponibles' : n + ' terrain disponible') + ' en découverte'
    terrains.forEach(t => dessiner(t, couche))
    liste.innerHTML = terrains.map(ligne).join('')
    if (couche.getLayers().length) carte.fitBounds(couche.getBounds(), { padding: [24, 24] })
  }).catch(() => {
    compte.textContent = 'La carte est momentanément indisponible. Réessayez dans quelques instants.'
  })
}

init()
})()
