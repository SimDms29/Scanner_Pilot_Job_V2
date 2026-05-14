import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getStatus } from '../api'

const UPDATES = [
  {
    date: 'Mai 2026',
    items: [
      'AstonJet ajouté (3 postes Captain Citation, Paris Le Bourget)',
      'Possibilité de trier les offres en fonction de leur date de publication',
      'Filtre Captain / F/O ajouté sur la page des offres',
      'GlobalJet intégré via Playwright (9 postes pilote : G650, Falcon 2000, PC24, A320ACJ…)',
      'DAS Private Jets ajouté (Phenom 300, Mengen)',
      'Arcus Air intégré (portail HubSpot)',
      '26 compagnies scannées au total',
    ],
  },
  {
    date: 'Avril 2026',
    items: [
      'Lancement de WingJobs en accès ouvert',
      'Première version avec 22 compagnies : VistaJet, Luxair, Loganair, Jet Aviation…',
      'Carte interactive Europe avec marqueurs par statut',
    ],
  },
]

function ActuModal({ onClose }) {
  return (
    <div className="wf-backdrop" onClick={onClose}>
      <div className="wf-modal actu-modal" onClick={e => e.stopPropagation()}>
        <button className="wf-close" onClick={onClose} aria-label="Fermer">✕</button>
        <div className="actu-title">Nouveautés</div>
        <div className="actu-list">
          {UPDATES.map(block => (
            <div key={block.date} className="actu-block">
              <div className="actu-date">{block.date}</div>
              <ul className="actu-items">
                {block.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const BASE_STATS = [
  { value: '27', label: 'Compagnies scannées' },
  { value: '12h', label: 'Fréquence de scan' },
]

const HOW = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
    title: 'Scan automatique',
    desc: '27 portails de recrutement parcourus toutes les 12 heures — BambooHR, Recruitee, Salesforce, Playwright pour les sites JS-rendus. Sans intervention manuelle.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    ),
    title: 'Détection en temps réel',
    desc: 'Chaque scan est comparé au précédent par signature de contenu. Une offre absente il y a 12h remonte immédiatement comme nouvelle.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/>
      </svg>
    ),
    title: 'Tout centralisé',
    desc: "Toutes les offres actives sur une interface unique — liste filtrée par source ou statut, carte interactive pour visualiser la répartition en Europe.",
  },
]

const SOURCES = [
  'VistaJet', 'GlobalJet', 'Luxair', 'Loganair', 'Jet Aviation', 'Gama Aviation',
  "Elit'Avia", 'Avcon Jet', 'TAG Aviation', 'DC Aviation', 'DAS Private Jets',
  'Widerøe', 'Spreeflug', 'GlobeAir', 'Arcus Air', 'Air Alliance', 'AstonJet', '+ 10 autres',
]

function WingFuelModal({ onClose }) {
  return (
    <div className="wf-backdrop" onClick={onClose}>
      <div className="wf-modal" onClick={e => e.stopPropagation()}>
        <button className="wf-close" onClick={onClose} aria-label="Fermer">✕</button>
        <div className="wf-logo">Wing<em>Fuel</em></div>
        <p className="wf-desc">
          Digitalisez votre gestion carburant, suivez votre consommation et optimisez vos coûts en aviation générale.
        </p>
        <ul className="wf-features">
          <li>Suivi de consommation par vol</li>
          <li>Tarifs carburant en temps réel</li>
          <li>Rapports et historique exportables</li>
        </ul>
        <a
          href="https://wingfuel.fr"
          target="_blank"
          rel="noreferrer"
          className="wf-cta"
          onClick={onClose}
        >
          Découvrir wingfuel.fr →
        </a>
      </div>
    </div>
  )
}

export default function Landing() {
  const [showWingFuel, setShowWingFuel] = useState(false)
  const [showActu, setShowActu] = useState(false)
  const [activeCount, setActiveCount] = useState(null)

  useEffect(() => {
    getStatus().then(d => setActiveCount(d.active ?? null)).catch(() => {})
  }, [])

  const stats = activeCount !== null
    ? [...BASE_STATS, { value: String(activeCount), label: 'Offres actives' }]
    : BASE_STATS

  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
          <div className="logo-text">
            <h1>Wing<em>Jobs</em></h1>
          </div>
        </Link>
        <div className="landing-nav-right">
          <button className="landing-nav-actu" onClick={() => setShowActu(true)}>
            Actu
          </button>
          <button className="landing-nav-wf" onClick={() => setShowWingFuel(true)}>
            Wing<em>Fuel</em>
          </button>
          <Link to="/jobs" className="landing-nav-link">Voir les offres →</Link>
        </div>
      </nav>

      {showWingFuel && <WingFuelModal onClose={() => setShowWingFuel(false)} />}
      {showActu && <ActuModal onClose={() => setShowActu(false)} />}

      {/* Hero */}
      <section className="hero-section">
        <div className="hero-bg-photos">
          <img className="hero-bg-photo" src="https://images.pexels.com/photos/30448307/pexels-photo-30448307.jpeg?auto=compress&cs=tinysrgb&w=1920" alt="" />
        </div>
        <div className="hero-overlay" />
        <div className="hero-blobs">
          <div className="blob blob-1" />
          <div className="blob blob-2" />
          <div className="blob blob-3" />
        </div>
        <div className="hero-content">
          <div className="landing-badge">Veille recrutement PNT · Business Aviation · Europe</div>

          <h2 className="landing-title">
            Les offres pilote que vous<br />n'aviez pas le temps de chercher
          </h2>

          <p className="landing-sub">
            WingJobs scanne automatiquement les portails de recrutement
            des compagnies d'aviation d'affaires européennes, toutes les 12 heures.
          </p>

          <div className="landing-stats">
            {stats.map(s => (
              <div key={s.label} className="landing-stat">
                <div className="landing-stat-val">{s.value}</div>
                <div className="landing-stat-lbl">{s.label}</div>
              </div>
            ))}
          </div>

          <Link to="/jobs" className="landing-cta">
            Voir les offres maintenant →
          </Link>
        </div>
      </section>

      {/* Comment ça marche */}
      <section className="landing-how">
        <div className="landing-how-inner">
          <p className="landing-section-label">Comment ça marche</p>
          <div className="landing-how-grid">
            {HOW.map((step, i) => (
              <div key={i} className="landing-how-card">
                <div className="landing-how-icon">{step.icon}</div>
                <h3 className="landing-how-title">{step.title}</h3>
                <p className="landing-how-desc">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sources */}
      <section className="landing-sources-section">
        <div className="landing-sources">
          <div className="landing-sources-lbl">Sources scannées</div>
          <div className="landing-sources-list">
            {SOURCES.map(s => (
              <span key={s} className="landing-source-chip">{s}</span>
            ))}
          </div>
        </div>
      </section>

      <div className="wingfuel-strip">
        <span className="wingfuel-strip-label">Par la même équipe —</span>
        <a href="https://wingfuel.fr" target="_blank" rel="noreferrer" className="wingfuel-strip-link">
          Wing<em>Fuel</em>
        </a>
        <span className="wingfuel-strip-desc">Suivi carburant pour l'aviation générale</span>
      </div>

      <footer className="landing-footer">
        <span>© 2026 Simon Dumas — WingJobs · Projet indépendant, non affilié aux compagnies listées</span>
      </footer>
    </div>
  )
}
