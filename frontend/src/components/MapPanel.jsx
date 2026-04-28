import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { divIcon } from 'leaflet'

function markerIcon(job) {
  let color = '#27e080', glow = 'rgba(39,224,128,0.5)'
  if (job.status === 'full')         { color = '#f0503a'; glow = 'rgba(240,80,58,0.4)' }
  else if (job.status === 'expired') { color = '#4a5f72'; glow = 'none' }
  else if (job.source === 'Amelia')  { color = '#a855f7'; glow = 'rgba(168,85,247,0.5)' }

  const svg = `<svg width="26" height="34" viewBox="0 0 26 34" xmlns="http://www.w3.org/2000/svg">
    <path d="M13 0C5.8 0 0 5.8 0 13C0 23 13 34 13 34C13 34 26 23 26 13C26 5.8 20.2 0 13 0Z" fill="${color}" opacity="0.93"/>
    <circle cx="13" cy="13" r="5" fill="rgba(0,0,0,0.4)"/>
  </svg>`
  return divIcon({
    html: `<div style="filter:drop-shadow(0 2px 8px ${glow})">${svg}</div>`,
    className: '',
    iconSize: [26, 34],
    iconAnchor: [13, 34],
    popupAnchor: [0, -36],
  })
}

// Flies to selected job and invalidates map size when panel resizes
function MapController({ jobs, selectedIdx, leftPct }) {
  const map = useMap()

  // Force resize on mount — Leaflet measures before flex layout is stable
  useEffect(() => {
    map.invalidateSize({ animate: false })
    const t = setTimeout(() => map.invalidateSize({ animate: false }), 400)
    return () => clearTimeout(t)
  }, [map])

  // Resize when drag handle moves
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize({ animate: false }), 50)
    return () => clearTimeout(t)
  }, [leftPct, map])

  useEffect(() => {
    if (selectedIdx === null) return
    const job = jobs[selectedIdx]
    if (job) map.flyTo([job.lat, job.lon], 8, { duration: 0.7 })
  }, [selectedIdx, jobs, map])

  return null
}

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR') + ' ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

// Deduplicate markers at same coords with slight offset
function offsetJobs(jobs) {
  const counts = {}
  return jobs.map((job) => {
    const key = `${parseFloat(job.lat).toFixed(2)}_${parseFloat(job.lon).toFixed(2)}`
    const n = counts[key] ?? 0
    counts[key] = n + 1
    return { ...job, lat: job.lat + n * 0.025, lon: job.lon + n * 0.025 }
  })
}

export default function MapPanel({ jobs, selectedIdx, onSelect, lastScan, nextScan, leftPct }) {
  const placed = offsetJobs(jobs)

  return (
    <div className="map-panel">
      <MapContainer
        className="map-container"
        center={[49, 8]}
        zoom={5}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={18} />
        <MapController jobs={jobs} selectedIdx={selectedIdx} leftPct={leftPct} />

        {placed.map((job, i) => (
          <Marker
            key={job.id + i}
            position={[job.lat, job.lon]}
            icon={markerIcon(job)}
            eventHandlers={{ click: () => onSelect(i) }}
          >
            <Popup maxWidth={300}>
              <div className="popup-source">{job.source}</div>
              <div className="popup-title">{job.title}</div>
              <div className="popup-loc">📍 {job.location}</div>
              {job.status === 'full'
                ? <span style={{ color: 'var(--red)', fontFamily: 'var(--mono)', fontSize: 11 }}>🔴 Effectifs complets</span>
                : <a className="popup-link" href={job.link} target="_blank" rel="noreferrer">Voir l'offre →</a>
              }
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="map-overlay top-right">
        <div className="legend-row"><span className="legend-dot" style={{ background: 'var(--green)', boxShadow: '0 0 5px var(--green-glow)' }} />Offre active</div>
        <div className="legend-row"><span className="legend-dot" style={{ background: 'var(--red)' }} />Effectifs complets</div>
        <div className="legend-row"><span className="legend-dot" style={{ background: 'var(--purple)' }} />Amelia</div>
      </div>

      {/* Scan info */}
      <div className="map-overlay bottom-left">
        <div><span className="live-dot" />En ligne</div>
        <div>Dernier scan : <span>{fmtDate(lastScan)}</span></div>
        <div>Prochain scan : <span>{fmtDate(nextScan)}</span></div>
      </div>
    </div>
  )
}
