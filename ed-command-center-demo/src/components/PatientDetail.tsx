import React from 'react'
import { Patient } from '../types'
import { generatePatientSummary } from '../lib/aiSim'
import TaskList from './TaskList'
import HandoffAssistant from './HandoffAssistant'

interface Props {
  patient: Patient | undefined
  onToggleTask: (taskId: string) => void
  onAddTask: (task: any) => void
}

export default function PatientDetail({ patient, onToggleTask, onAddTask }: Props) {
  if (!patient) return <div className="patient-empty">Select a patient to view details</div>

  const summary = generatePatientSummary(patient)

  return (
    <div className="patient-detail">
      <header className="pd-header">
        <div>
          <h2>{patient.name} <small>{patient.age}yo</small></h2>
          <div className="meta">{patient.sex} • ESI {patient.triageLevel} • {patient.location} • {Math.floor(patient.timeInEDMinutes/60)}h {patient.timeInEDMinutes%60}m</div>
        </div>
      </header>

      <section className="card">
        <div className="card-title">AI-generated draft – for demo only</div>
        <p>{summary}</p>
      </section>

      <section className="card">
        <div className="card-title">Timeline</div>
        <ul>
          {patient.events.slice().reverse().map(e => (
            <li key={e.timestamp}><strong>{new Date(e.timestamp).toLocaleString()}:</strong> {e.type} — {e.description}</li>
          ))}
        </ul>
      </section>

      <section className="card">
        <div className="card-title">Tasks</div>
        <TaskList tasks={patient.tasks} onToggle={onToggleTask} onAdd={onAddTask} />
      </section>

      <section className="card">
        <div className="card-title">Handoff Assistant</div>
        <HandoffAssistant patient={patient} />
      </section>
    </div>
  )
}
