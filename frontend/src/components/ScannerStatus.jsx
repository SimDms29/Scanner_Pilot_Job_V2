import { useState } from 'react'

function dotClass(s) {
  if (s.status === 'error') return 'error'
  return s.jobs_found > 0 ? 'ok-jobs' : 'ok-empty'
}

function fmtDur(ms) {
  if (!ms) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export default function ScannerStatus({ sources }) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <div className="scanner-bar" onClick={() => setOpen(o => !o)}>
        <div className="scanner-bar-left">
          <span className="scanner-bar-label">Sources</span>
          <div className="health-dots">
            {sources.map(s => (
              <span
                key={s.source}
                className={`health-dot ${dotClass(s)}`}
                title={`${s.source} — ${s.status === 'error' ? (s.error_msg || 'erreur') : s.jobs_found + ' offre(s)'}`}
              />
            ))}
          </div>
        </div>
        <span className={`scanner-chevron ${open ? 'open' : ''}`}>▼</span>
      </div>

      <div className={`scanner-panel ${open ? 'open' : ''}`}>
        {sources.length === 0 ? (
          <div className="source-row" style={{ color: 'var(--text-dim)' }}>Aucune donnée — lancez un scan.</div>
        ) : sources.map(s => {
          const cls = dotClass(s)
          return (
            <div key={s.source} className="source-row">
              <span className={`source-dot ${cls}`} />
              <span className="source-name">{s.source}</span>
              {s.status === 'error'
                ? <span className="source-err">{s.error_msg || 'erreur réseau'}</span>
                : <span className="source-count">{s.jobs_found} offre{s.jobs_found !== 1 ? 's' : ''}</span>
              }
              <span className="source-dur">{fmtDur(s.duration_ms)}</span>
            </div>
          )
        })}
      </div>
    </>
  )
}
