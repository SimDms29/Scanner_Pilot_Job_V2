import { useState, useEffect, useCallback, useRef } from 'react'
import { getJobs, getSources, getStatus, getScannerStatus, triggerScan } from './api'
import Header from './components/Header'
import FilterBar from './components/FilterBar'
import ScannerStatus from './components/ScannerStatus'
import JobList from './components/JobList'
import MapPanel from './components/MapPanel'

const DEFAULT_FILTERS = { q: '', source: '', status: 'active' }

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
  const dragging = useRef(false)

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

  // Drag handle
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
        <div className="left" style={{ width: `${leftPct}%` }}>
          <FilterBar sources={sources} filters={filters} onChange={setFilters} />
          <ScannerStatus sources={scannerSrcs} />
          <div className="count-bar">
            {jobs.length} offre{jobs.length !== 1 ? 's' : ''} affichée{jobs.length !== 1 ? 's' : ''}
          </div>
          <JobList jobs={jobs} selectedIdx={selectedIdx} onSelect={setSelectedIdx} />
        </div>

        <div className="drag-handle" onMouseDown={() => { dragging.current = true }} />

        <div className="right">
          <MapPanel
            jobs={jobs}
            selectedIdx={selectedIdx}
            onSelect={setSelectedIdx}
            lastScan={lastScan}
            nextScan={nextScan}
            leftPct={leftPct}
          />
        </div>
      </div>
    </div>
  )
}
