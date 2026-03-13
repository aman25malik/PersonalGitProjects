import React, { useEffect, useState } from 'react'
import { Patient } from '../types'
import { generateHandoff } from '../lib/aiSim'

interface Props {
  patient: Patient
}

export default function HandoffAssistant({ patient }: Props) {
  const [draft, setDraft] = useState(() => generateHandoff(patient))

  useEffect(() => {
    setDraft(generateHandoff(patient))
  }, [patient])

  function regenerate() {
    setDraft(generateHandoff(patient))
  }

  async function copyAll() {
    const text = `IDENTIFICATION:\n${draft.identification}\n\nSITUATION:\n${draft.situation}\n\nBACKGROUND:\n${draft.background}\n\nASSESSMENT:\n${draft.assessment}\n\nRECOMMENDATION:\n${draft.recommendation}`
    try {
      await navigator.clipboard.writeText(text)
      alert('Copied to clipboard')
    } catch (err) {
      alert('Copy failed')
    }
  }

  return (
    <div className="handoff">
      <div className="handoff-actions">
        <button onClick={regenerate}>Regenerate draft</button>
        <button onClick={copyAll}>Copy to clipboard</button>
      </div>

      <div className="handoff-grid">
        <div>
          <label>Identification</label>
          <textarea value={draft.identification} onChange={e => setDraft(prev => ({ ...prev, identification: e.target.value }))} />
        </div>
        <div>
          <label>Situation</label>
          <textarea value={draft.situation} onChange={e => setDraft(prev => ({ ...prev, situation: e.target.value }))} />
        </div>
        <div>
          <label>Background</label>
          <textarea value={draft.background} onChange={e => setDraft(prev => ({ ...prev, background: e.target.value }))} />
        </div>
        <div>
          <label>Assessment</label>
          <textarea value={draft.assessment} onChange={e => setDraft(prev => ({ ...prev, assessment: e.target.value }))} />
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <label>Recommendation</label>
          <textarea value={draft.recommendation} onChange={e => setDraft(prev => ({ ...prev, recommendation: e.target.value }))} />
        </div>
      </div>
    </div>
  )
}
