import { Link } from 'react-router-dom'

export default function Header({ stats }) {
  return (
    <header className="header">
      <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
        <svg className="logo-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
        </svg>
        <div className="logo-text">
          <h1>Wing<em>Jobs</em></h1>
          <small>Veille recrutement PNT · Europe</small>
        </div>
      </Link>

      <div className="header-right">
        <div className="stats">
          <div className="stat">
            <div className="stat-val green">{stats.active ?? '—'}</div>
            <div><span className="stat-lbl">Actives</span></div>
          </div>
          <div className="stat">
            <div className="stat-val amber">{stats.total ?? '—'}</div>
            <div><span className="stat-lbl">Total</span></div>
          </div>
          <div className="stat">
            <div className="stat-val red">{stats.new_48h ?? '—'}</div>
            <div><span className="stat-lbl">Nouvelles</span></div>
          </div>
        </div>
      </div>
    </header>
  )
}
