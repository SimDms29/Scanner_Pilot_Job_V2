import { useState, useEffect, useCallback, useRef } from 'react'
import { getJobs, getSources, getStatus, getScannerStatus, triggerScan } from './api'
import Header from './components/Header'
import FilterBar from './components/FilterBar'
import ScannerStatus from './components/ScannerStatus'
import JobList from './components/JobList'
import MapPanel from './components/MapPanel'

const DEFAULT_FILTERS = { q: '', source: '', status: 'active' }
const MOBILE_BP = 768

export default function App() {
  const [jobs, setJobs] = useState([])
  const [sources, setSources] = useState([])
  const [scannerSrcs, setScannerSrcs] = useState([])
  const [stats, setStats] = useState({ active: 0, total: 0, new_48h: 0 })
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [scanRunning, setScanRunning] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState(null)
  const [lastScan, setLastScan] = useState(null)
  const [nextScan, setNextScan] = useState(null)
  const [leftPct, setLeftPct] = useState(35)
  const [activeTab, setActiveTab] = useState('list')
  const dragging = useRef(false)

  const isMobile = () => window.innerWidth <= MOBILE_BP

  const loadJobs = useCallback(async () => {
    const data = await getJobs(filters)
    setJobs(data)
  }, [filters])

  const loadMeta = useCallback(async () => {
    const [srcs, scannerData, statusData] = await Promise.all([
      getSources(),
      getScannerStatus(),
      getStatus(),
    ])
    setSources(srcs)
    setScannerSrcs(scannerData)
    setLastScan(statusData.last_scan)
    setNextScan(statusData.next_scan)
    setScanRunning(statusData.scan_running)
    setStats({
      active: statusData.active ?? 0,
      total: statusData.total ?? 0,
      new_48h: statusData.new_48h ?? 0,
    })
  }, [])

  useEffect(() => { loadJobs() }, [loadJobs])
  useEffect(() => { loadMeta() }, [loadMeta])

  const pollScan = useCallback(() => {
    const iv = setInterval(async () => {
      const s = await getStatus()
      if (!s.scan_running) {
        clearInterval(iv)
        setScanRunning(false)
        await Promise.all([loadJobs(), loadMeta()])
      }
    }, 1500)
  }, [loadJobs, loadMeta])

  const handleScan = useCallback(async () => {
    if (scanRunning) return
    setScanRunning(true)
    await triggerScan()
    pollScan()
  }, [scanRunning, pollScan])

  const handleSelect = useCallback((idx) => {
    setSelectedIdx(idx)
    if (isMobile()) setActiveTab('map')
  }, [])

  // Drag handle (desktop only)
  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return
      const pct = (e.clientX / window.innerWidth) * 100
      setLeftPct(Math.max(20, Math.min(60, pct)))
    }
    const onUp = () => { dragging.current = false }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
  }, [])

  return (
    <div className="app">
      <Header stats={stats} scanRunning={scanRunning} onScan={handleScan} />

      <div className="body">
        <div className={`left${activeTab === 'map' ? ' mob-hidden' : ''}`} style={{ width: `${leftPct}%` }}>
          <FilterBar sources={sources} filters={filters} onChange={setFilters} />
          <ScannerStatus sources={scannerSrcs} />
          <div className="count-bar">
            {jobs.length} offre{jobs.length !== 1 ? 's' : ''} affichée{jobs.length !== 1 ? 's' : ''}
          </div>
          <JobList jobs={jobs} selectedIdx={selectedIdx} onSelect={handleSelect} />
        </div>

        <div className="drag-handle" onMouseDown={() => { dragging.current = true }} />

        <div className={`right${activeTab === 'list' ? ' mob-hidden' : ''}`}>
          <MapPanel
            jobs={jobs}
            selectedIdx={selectedIdx}
            onSelect={handleSelect}
            lastScan={lastScan}
            nextScan={nextScan}
            leftPct={leftPct}
          />
        </div>
      </div>

      {/* Tab bar — mobile only */}
      <nav className="tab-bar">
        <button className={`tab-btn${activeTab === 'list' ? ' active' : ''}`} onClick={() => setActiveTab('list')}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h18v2H3v-2z"/>
          </svg>
          Offres
        </button>
        <button className={`tab-btn${activeTab === 'map' ? ' active' : ''}`} onClick={() => setActiveTab('map')}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
          Carte
        </button>
      </nav>
    </div>
  )
}
