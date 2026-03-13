import React, { useMemo, useState, useRef, useEffect } from 'react'
import CommandBoard from './components/CommandBoard'
import PatientDetail from './components/PatientDetail'
import initialPatients from './data/mockData'
import { Patient, Task } from './types'
import { v4 as uuidv4 } from 'uuid'
import { startMockIncomingPredictions, startMockOutgoingAggregator } from './lib/integration'

export default function App() {
  const [patients, setPatients] = useState<Patient[]>(initialPatients)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<{ triage?: number | null; risk?: string | null; mineOnly?: boolean }>({})
  const currentUser = 'Dr. Smith'
  const [lastIncoming, setLastIncoming] = useState<string | null>(null)
  const [lastOutgoing, setLastOutgoing] = useState<string | null>(null)
  const [lastOutgoingStatus, setLastOutgoingStatus] = useState<string | null>(null)

  const patientsRef = useRef<Patient[]>(patients)
  useEffect(() => { patientsRef.current = patients }, [patients])

  const selected = useMemo(() => patients.find(p => p.id === selectedId)!, [patients, selectedId])

  function toggleTask(taskId: string) {
    setPatients(prev => prev.map(p => ({
      ...p,
      tasks: p.tasks.map(t => t.id === taskId ? { ...t, status: t.status === 'done' ? 'pending' : 'done' } : t)
    })))
  }

  function addTaskForSelected(task: Omit<Task, 'id' | 'status'> & { status?: Task['status'] }) {
    if (!selectedId) return
    const newTask: Task = {
      id: uuidv4(),
      description: task.description,
      ownerRole: task.ownerRole,
      dueInMinutes: task.dueInMinutes,
      status: task.status ?? 'pending',
      priority: task.priority
    }
    setPatients(prev => prev.map(p => p.id === selectedId ? { ...p, tasks: [...p.tasks, newTask] } : p))
  }

  // start demo integrations (incoming predictions + outgoing aggregator)
  useEffect(() => {
    const stopIncoming = startMockIncomingPredictions(setPatients as any, setLastIncoming)
    const stopOutgoing = startMockOutgoingAggregator(() => patientsRef.current, setLastOutgoing, setLastOutgoingStatus)
    return () => { stopIncoming(); stopOutgoing() }
  }, [])

  return (
    <div className="app-shell">
      <div className="topbar" style={{position:'absolute',left:16,top:8,right:16}}>
        <small style={{color:'#475569'}}>Last predictions update: {lastIncoming ?? '—'} • Last bedside sync: {lastOutgoing ?? '—'} {lastOutgoingStatus ? `(${lastOutgoingStatus})` : ''}</small>
      </div>
      <div className="left">
        <div className="controls">
          <div>
            <label>Filters:</label>
            <select onChange={e => setFilters(f => ({ ...f, triage: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">All Triage</option>
              <option value="1">ESI 1</option>
              <option value="2">ESI 2</option>
              <option value="3">ESI 3</option>
              <option value="4">ESI 4</option>
              <option value="5">ESI 5</option>
            </select>
            <select onChange={e => setFilters(f => ({ ...f, risk: e.target.value || undefined }))}>
              <option value="">All Risk</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
            <label><input type="checkbox" onChange={e => setFilters(f => ({ ...f, mineOnly: e.target.checked }))} /> My patients</label>
          </div>
        </div>

        <CommandBoard patients={patients} onSelect={id => setSelectedId(id)} currentUser={currentUser} filters={filters} setSearch={setSearch} search={search} />
      </div>

      {selectedId && (
        <div className="detail-drawer-wrap">
          <div className="drawer-backdrop" onClick={() => setSelectedId(null)} />
          <div className="detail-drawer">
            <button className="drawer-close" onClick={() => setSelectedId(null)}>Close ✕</button>
            <PatientDetail patient={selected} onToggleTask={toggleTask} onAddTask={addTaskForSelected} />
          </div>
        </div>
      )}
    </div>
  )
}
