import JobCard from './JobCard'

export default function JobList({ jobs, selectedIdx, onSelect }) {
  if (!jobs.length) {
    return (
      <div className="jobs-list">
        <div className="empty-state">Aucune offre ne correspond<br />à votre recherche.</div>
      </div>
    )
  }

  // Group by source
  const groups = {}
  jobs.forEach((job, i) => {
    ;(groups[job.source] = groups[job.source] || []).push({ job, i })
  })

  return (
    <div className="jobs-list">
      {Object.entries(groups).map(([src, items]) => (
        <div key={src}>
          <div className="group-header">
            {src} &nbsp;·&nbsp; {items.length} offre{items.length > 1 ? 's' : ''}
          </div>
          {items.map(({ job, i }) => (
            <JobCard
              key={job.id}
              job={job}
              highlighted={selectedIdx === i}
              onClick={() => onSelect(i)}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
