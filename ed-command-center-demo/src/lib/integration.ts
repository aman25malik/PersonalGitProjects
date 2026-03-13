import mockPredictions from '../data/mockOpsPredictions.json'
import { Patient } from '../types'

type SetPatients = (updater: (prev: Patient[]) => Patient[]) => void

export function startMockIncomingPredictions(setPatients: SetPatients, setLastIncoming: (s: string) => void) {
  // Apply the mock predictions periodically to simulate an ops command center pushing predictions
  const apply = () => {
    const ts = new Date().toISOString()
    setPatients(prev => prev.map(p => {
      const pred = (mockPredictions as any[]).find(x => x.patientId === p.id)
      if (!pred) return { ...p, externalPredictions: undefined }
      return { ...p, externalPredictions: { deteriorationScore: pred.deteriorationScore, admissionProbability: pred.admissionProbability, source: pred.source, timestamp: ts } }
    }))
    setLastIncoming(new Date().toLocaleTimeString())
  }

  apply()
  const id = setInterval(() => apply(), 10_000)
  return () => clearInterval(id)
}

export function startMockOutgoingAggregator(getPatients: () => Patient[], setLastOutgoing: (s: string) => void, setLastOutgoingStatus: (s: string) => void) {
  // Periodically compose an aggregated bedside summary and "send" it to a simulated POST endpoint.
  const simulatePost = async (payload: any) => {
    // simulate network latency and random failure for demo
    const delay = 400 + Math.floor(Math.random() * 800)
    await new Promise(res => setTimeout(res, delay))
    const success = Math.random() > 0.12 // ~88% success
    if (success) return { ok: true, status: 200, message: 'OK' }
    return { ok: false, status: 500, message: 'Simulated server error' }
  }

  const send = async () => {
    const pts = getPatients()
    const readyForDispo = pts.filter(p => p.tasks.every(t => t.status === 'done')).length
    const blockedOnImaging = pts.filter(p => p.events.some(e => /CT|XR|CXR|Ultrasound/i.test(e.type)) && p.tasks.some(t => t.status !== 'done')).length
    const overdueHighTasks = pts.flatMap(p => p.tasks.filter(t => t.priority === 'high' && t.status !== 'done' && t.dueInMinutes <= 0).map(t => ({ patientId: p.id, taskId: t.id, desc: t.description })))

    const payload = {
      unit: 'ED-PodA',
      timestamp: new Date().toISOString(),
      readyForDispo,
      blockedOnImaging,
      overdueHighTasks
    }

    setLastOutgoing(new Date().toLocaleTimeString())
    try {
      const resp = await simulatePost(payload)
      if (resp.ok) {
        setLastOutgoingStatus(`OK ${resp.status}`)
      } else {
        setLastOutgoingStatus(`ERR ${resp.status}`)
      }
    } catch (err: any) {
      setLastOutgoingStatus('ERR')
    }
  }

  send()
  const id = setInterval(() => send(), 15_000)
  return () => clearInterval(id)
}
