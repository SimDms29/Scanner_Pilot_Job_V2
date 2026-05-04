import { Link } from 'react-router-dom'

const STATS = [
  { value: '26', label: 'Compagnies scannées' },
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
    desc: '26 portails de recrutement parcourus toutes les 12 heures — BambooHR, Recruitee, Salesforce, Playwright pour les sites JS-rendus. Sans intervention manuelle.',
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
  'Widerøe', 'Spreeflug', 'GlobeAir', 'Arcus Air', 'Air Alliance', '+ 10 autres',
]

export default function Landing() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
          <svg className="logo-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
          </svg>
          <div className="logo-text">
            <h1>Wing<em>Jobs</em></h1>
          </div>
        </Link>
        <Link to="/jobs" className="landing-nav-link">Voir les offres →</Link>
      </nav>

      {/* Hero */}
      <main className="landing-main">
        <div className="landing-badge">Veille recrutement PNT · Business Aviation · Europe</div>

        <h2 className="landing-title">
          Les offres pilote que vous<br />n'aviez pas le temps de chercher
        </h2>

        <p className="landing-sub">
          WingJobs scanne automatiquement les portails de recrutement
          des compagnies d'aviation d'affaires européennes, toutes les 12 heures.
        </p>

        <div className="landing-stats">
          {STATS.map(s => (
            <div key={s.label} className="landing-stat">
              <div className="landing-stat-val">{s.value}</div>
              <div className="landing-stat-lbl">{s.label}</div>
            </div>
          ))}
        </div>

        <Link to="/jobs" className="landing-cta">
          Voir les offres maintenant →
        </Link>
      </main>

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

      <footer className="landing-footer">
        <span>© 2026 Simon Dumas — WingJobs · Projet indépendant, non affilié aux compagnies listées</span>
      </footer>
    </div>
  )
}
