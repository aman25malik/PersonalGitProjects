import React, { useState } from 'react'
import { Task } from '../types'
import { minutesToRelative } from '../lib/aiSim'

interface Props {
  tasks: Task[]
  onToggle: (taskId: string) => void
  onAdd: (task: Omit<Task, 'id' | 'status'> & { status?: Task['status'] }) => void
}

export default function TaskList({ tasks, onToggle, onAdd }: Props) {
  const [desc, setDesc] = useState('')
  const [owner, setOwner] = useState<'MD'|'RN'|'Resident'|'Tech'>('RN')
  const [priority, setPriority] = useState<'low'|'medium'|'high'>('medium')
  const [due, setDue] = useState<number>(30)

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!desc.trim()) return
    onAdd({ description: desc.trim(), ownerRole: owner, priority, dueInMinutes: due, status: 'pending' })
    setDesc('')
  }

  return (
    <div className="task-list">
      <ul>
        {tasks.map(t => (
          <li key={t.id} className={`task-item ${t.priority}`}>
            <label>
              <input type="checkbox" checked={t.status === 'done'} onChange={() => onToggle(t.id)} />
              <span className="task-desc">{t.description}</span>
            </label>
            <div className="task-meta">
              <span className="pill">{t.ownerRole}</span>
              <span className="pill">{t.priority}</span>
              <span className="due">{minutesToRelative(t.dueInMinutes)}</span>
            </div>
          </li>
        ))}
      </ul>

      <form className="add-task" onSubmit={submit}>
        <input placeholder="New task description" value={desc} onChange={e => setDesc(e.target.value)} />
        <select value={owner} onChange={e => setOwner(e.target.value as any)}>
          <option>RN</option>
          <option>MD</option>
          <option>Resident</option>
          <option>Tech</option>
        </select>
        <select value={priority} onChange={e => setPriority(e.target.value as any)}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
        <input type="number" value={due} onChange={e => setDue(Number(e.target.value))} />
        <button type="submit">Add</button>
      </form>
    </div>
  )
}
