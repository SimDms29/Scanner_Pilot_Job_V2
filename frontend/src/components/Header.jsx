export default function Header({ stats, scanRunning, onScan }) {
  return (
    <header className="header">
      <div className="logo">
        <svg className="logo-icon" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <path d="M50 8 L92 62 L74 56 L68 88 L50 76 L32 88 L26 56 L8 62 Z" />
        </svg>
        <div className="logo-text">
          <h1>Wing<em>Jobs</em></h1>
          <small>Veille recrutement PNT · Europe</small>
        </div>
      </div>

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

        <button className="btn-scan" disabled={scanRunning} onClick={onScan}>
          {scanRunning
            ? <><span className="spin">◌</span> Scan en cours</>
            : <>⟳ Scanner</>
          }
        </button>
      </div>
    </header>
  )
}
