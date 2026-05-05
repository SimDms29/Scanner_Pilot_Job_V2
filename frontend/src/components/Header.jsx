import { Link } from 'react-router-dom'

export default function Header({ stats }) {
  return (
    <header className="header">
      <Link to="/" className="logo" style={{ textDecoration: 'none' }}>
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
