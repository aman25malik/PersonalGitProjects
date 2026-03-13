import { Patient } from '../types'

export type RiskLevel = 'low' | 'medium' | 'high'

export function computeRiskLevel(p: Patient): RiskLevel {
  let score = 0
  if (p.triageLevel <= 2) score += 3
  if (p.vitalsFlags.length > 0) score += p.vitalsFlags.length * 2
  if (p.timeInEDMinutes > 240) score += 2
  const highPending = p.tasks.filter(t => t.priority === 'high' && t.status !== 'done' && t.dueInMinutes <= 0).length
  score += Math.min(3, highPending * 2)

  if (score >= 6) return 'high'
  if (score >= 3) return 'medium'
  return 'low'
}

export function minutesToRelative(mins: number) {
  if (mins < 0) return `Overdue by ${Math.abs(mins)} min`
  if (mins < 60) return `Due in ${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return `Due in ${h}h ${m}m`
}

export function generatePatientSummary(p: Patient): string {
  const risk = computeRiskLevel(p)
  const problems = p.vitalsFlags.length ? p.vitalsFlags.join(', ') : 'no major vital flags'
  const pendingHigh = p.tasks.filter(t => t.priority === 'high' && t.status !== 'done')
  const urgent = pendingHigh.length ? `There are ${pendingHigh.length} high-priority tasks outstanding.` : 'No outstanding high-priority tasks.'

  const plan = p.dispositionEstimate ? `Plan: ${p.dispositionEstimate}.` : ''

  const sentence1 = `${p.name}, ${p.age}yo, presents with ${p.chiefComplaint}.` 
  const sentence2 = `Notable: ${problems}. ${urgent}`
  const sentence3 = `Risk assessment: ${risk.toUpperCase()}. ${plan}`

  return `${sentence1} ${sentence2} ${sentence3}`
}

export function generateHandoff(p: Patient) {
  const id = `Patient: ${p.name}, ${p.age}yo (${p.sex}). Location: ${p.location}.` 
  const situation = `Here for ${p.chiefComplaint}. Time in ED: ${Math.floor(p.timeInEDMinutes/60)}h ${p.timeInEDMinutes%60}m.`
  const background = `Triage ESI ${p.triageLevel}. Vitals flags: ${p.vitalsFlags.length ? p.vitalsFlags.join(', ') : 'none'}. Events: ${p.events.slice(-3).map(e => e.type).join(', ')}.`
  const assessment = `${generatePatientSummary(p)}`
  const recs = p.tasks.filter(t => t.status !== 'done').map(t => `- ${t.description} (owner: ${t.ownerRole}, ${t.priority})`).join('\n') || 'No outstanding tasks.'

  return {
    identification: id,
    situation,
    background,
    assessment,
    recommendation: recs
  }
}

export function deriveStatusFromTasksAndEvents(p: Patient): string {
  const pending = p.tasks.filter(t => t.status !== 'done')
  if (pending.some(t => t.priority === 'high')) return 'Pending high-priority tasks'
  if (p.events.some(e => /CT|XR|CXR|Ultrasound/i.test(e.type))) return 'Awaiting imaging results'
  return pending.length ? 'Pending tasks' : 'Ready for dispo'
}
