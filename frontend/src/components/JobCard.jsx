function isNew(firstSeen) {
  if (!firstSeen) return false
  return Date.now() - new Date(firstSeen).getTime() < 48 * 3600 * 1000
}

const STATUS_LABEL = { active: 'Actif', full: 'Complet', expired: 'Expiré' }

export default function JobCard({ job, highlighted, onClick }) {
  const classes = [
    'job-card',
    `status-${job.status}`,
    highlighted ? 'highlighted' : '',
  ].filter(Boolean).join(' ')

  const fresh = isNew(job.first_seen)

  return (
    <div className={classes} onClick={onClick}>
      <div className={`status-dot ${job.status}`} />

      <div className="card-body">
        <div className="card-top">
          <span className="card-source">{job.source}</span>
          <div className="card-badges">
            {fresh && <span className="badge badge-new">Nouveau</span>}
            <span className={`badge badge-${job.status}`}>
              {STATUS_LABEL[job.status] ?? job.status}
            </span>
          </div>
        </div>

        <div className="card-title">{job.title}</div>

        <div className="card-bottom">
          <span className="card-location">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="var(--text-dim)" style={{ flexShrink: 0 }}>
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            {job.location}
          </span>
          {job.status !== 'full' && (
            <a
              className="card-link"
              href={job.link}
              target="_blank"
              rel="noreferrer"
              onClick={e => e.stopPropagation()}
            >
              Voir l'offre →
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
