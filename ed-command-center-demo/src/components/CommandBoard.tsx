import React from 'react'
import { Patient } from '../types'
import { computeRiskLevel, deriveStatusFromTasksAndEvents } from '../lib/aiSim'

interface Props {
  patients: Patient[]
  onSelect: (id: string) => void
  currentUser: string
  filters: { triage?: number | null; risk?: string | null; mineOnly?: boolean }
  setSearch: (s: string) => void
  search: string
}

function timeDisplay(mins: number) {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return `${h}h ${m}m`
}

export default function CommandBoard({ patients, onSelect, currentUser, filters, setSearch, search }: Props) {
  const filtered = patients.filter(p => {
    if (filters.triage && p.triageLevel !== filters.triage) return false
    if (filters.risk) {
      const r = computeRiskLevel(p)
      if (r !== filters.risk) return false
    }
    if (filters.mineOnly && p.primaryPhysician !== currentUser) return false
    if (search) {
      const s = search.toLowerCase()
      if (!p.name.toLowerCase().includes(s) && !p.chiefComplaint.toLowerCase().includes(s)) return false
    }
    return true
  })

  return (
    <div className="board">
      <div className="board-header">
        <input placeholder="Search name or complaint..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <table className="patient-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Age</th>
            <th>Triage</th>
            <th>Complaint</th>
            <th>Time</th>
            <th>Risk</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(p => {
            const risk = computeRiskLevel(p)
            const status = deriveStatusFromTasksAndEvents(p)
            const hasOverdueHigh = p.tasks.some(t => t.priority === 'high' && t.dueInMinutes <= 0 && t.status !== 'done')
            return (
              <tr key={p.id} className={`patient-row ${hasOverdueHigh ? 'overdue' : ''}`} onClick={() => onSelect(p.id)}>
                <td>
                  {p.name}{hasOverdueHigh && <span className="dot" title="Overdue high priority"></span>}
                  {p.externalPredictions && <span style={{marginLeft:8, fontSize:12, color:'#1e293b'}} title={`External: ${p.externalPredictions.source}`}>• ext</span>}
                </td>
                <td>{p.age}</td>
                <td><span className={`badge triage triage-${p.triageLevel}`}>ESI {p.triageLevel}</span></td>
                <td>{p.chiefComplaint}</td>
                <td>{timeDisplay(p.timeInEDMinutes)}</td>
                <td><span className={`badge risk-${risk}`}>{risk}</span></td>
                <td>{status}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
