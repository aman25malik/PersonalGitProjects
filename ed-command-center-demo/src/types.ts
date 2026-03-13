export type TaskStatus = 'pending' | 'in_progress' | 'done'

export interface Task {
  id: string
  description: string
  ownerRole: 'MD' | 'RN' | 'Resident' | 'Tech'
  dueInMinutes: number
  status: TaskStatus
  priority: 'low' | 'medium' | 'high'
}

export interface EventItem {
  timestamp: string
  type: string
  description: string
}

export interface Patient {
  id: string
  name: string
  age: number
  sex: 'M' | 'F' | 'Other'
  triageLevel: number
  chiefComplaint: string
  timeInEDMinutes: number
  location: string
  primaryPhysician: string
  vitalsFlags: string[]
  dispositionEstimate: string
  events: EventItem[]
  tasks: Task[]
  externalPredictions?: {
    deteriorationScore?: number
    admissionProbability?: number
    source?: string
    timestamp?: string
  }
}
