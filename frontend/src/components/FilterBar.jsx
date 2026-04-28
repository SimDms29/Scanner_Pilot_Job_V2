export default function FilterBar({ sources, filters, onChange }) {
  const set = (key, val) => onChange(prev => ({ ...prev, [key]: val }))

  return (
    <div className="filters-bar">
      <div className="filter-group">
        <span className="filter-lbl">Recherche</span>
        <input
          className="search-input"
          type="text"
          placeholder="Titre, ville, appareil..."
          value={filters.q}
          onChange={e => set('q', e.target.value)}
        />
      </div>

      <div className="sep" />

      <div className="filter-group">
        <span className="filter-lbl">Source</span>
        <div className="chips">
          <button
            className={`chip ${filters.source === '' ? 'active' : ''}`}
            onClick={() => set('source', '')}
          >Toutes</button>
          {sources.map(s => (
            <button
              key={s}
              className={`chip ${filters.source === s ? 'active' : ''}`}
              onClick={() => set('source', s)}
            >{s}</button>
          ))}
        </div>
      </div>

      <div className="sep" />

      <div className="filter-group">
        <span className="filter-lbl">Statut</span>
        <div className="chips">
          {[['all', 'Tous', ''], ['active', 'Actives', ''], ['full', 'Complètes', 'chip-red'], ['expired', 'Expirées', 'chip-red']].map(([val, label, extra]) => (
            <button
              key={val}
              className={`chip ${extra} ${filters.status === val ? 'active' : ''}`}
              onClick={() => set('status', val)}
            >{label}</button>
          ))}
        </div>
      </div>
    </div>
  )
}
