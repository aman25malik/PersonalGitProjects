import { Patient } from '../types'

// Small helper to create task ids
const tid = (n: number) => `${n}-${Math.floor(Math.random() * 10000)}`

export const patients: Patient[] = [
  {
    id: 'p1',
    name: 'John Doe',
    age: 67,
    sex: 'M',
    triageLevel: 2,
    chiefComplaint: 'Shortness of breath',
    timeInEDMinutes: 180,
    location: 'Room 3',
    primaryPhysician: 'Dr. Smith',
    vitalsFlags: ['tachycardic'],
    dispositionEstimate: 'Likely admit',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(), type: 'Arrived', description: 'Patient arrived via ambulance' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 160).toISOString(), type: 'CT', description: 'CT chest ordered' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 140).toISOString(), type: 'Lab', description: 'CBC, BMP drawn' }
    ],
    tasks: [
      { id: tid(1), description: 'Start IV and give 1L bolus', ownerRole: 'RN', dueInMinutes: -10, status: 'pending', priority: 'high' },
      { id: tid(2), description: 'Discuss with admitting service', ownerRole: 'MD', dueInMinutes: 60, status: 'pending', priority: 'medium' }
    ]
  },
  {
    id: 'p2',
    name: 'Mary Johnson',
    age: 45,
    sex: 'F',
    triageLevel: 3,
    chiefComplaint: 'Abdominal pain',
    timeInEDMinutes: 90,
    location: 'Room 7',
    primaryPhysician: 'Dr. Lee',
    vitalsFlags: [],
    dispositionEstimate: 'Likely discharge',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(), type: 'Arrived', description: 'Self-presented' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), type: 'Ultrasound', description: 'RUQ ultrasound completed' }
    ],
    tasks: [
      { id: tid(3), description: 'Pain control meds', ownerRole: 'RN', dueInMinutes: 15, status: 'in_progress', priority: 'medium' }
    ]
  },
  {
    id: 'p3',
    name: 'Carlos Martinez',
    age: 29,
    sex: 'M',
    triageLevel: 4,
    chiefComplaint: 'Laceration to forearm',
    timeInEDMinutes: 35,
    location: 'Procedure Bay',
    primaryPhysician: 'Dr. Smith',
    vitalsFlags: [],
    dispositionEstimate: 'Likely discharge',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 40).toISOString(), type: 'Arrived', description: 'Walk-in with laceration' }
    ],
    tasks: [
      { id: tid(4), description: 'Suture wound', ownerRole: 'Resident', dueInMinutes: 20, status: 'pending', priority: 'medium' }
    ]
  },
  {
    id: 'p4',
    name: 'Aisha Khan',
    age: 82,
    sex: 'F',
    triageLevel: 2,
    chiefComplaint: 'Confusion, possible UTI',
    timeInEDMinutes: 300,
    location: 'Room 1',
    primaryPhysician: 'Dr. Patel',
    vitalsFlags: ['hypotensive'],
    dispositionEstimate: 'ICU possible',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 300).toISOString(), type: 'Arrived', description: 'Family brought patient' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 240).toISOString(), type: 'Labs', description: 'UA and blood cultures sent' }
    ],
    tasks: [
      { id: tid(5), description: 'Blood cultures x2', ownerRole: 'RN', dueInMinutes: -60, status: 'pending', priority: 'high' },
      { id: tid(6), description: 'Start broad-spectrum antibiotics', ownerRole: 'MD', dueInMinutes: 10, status: 'pending', priority: 'high' }
    ]
  },
  {
    id: 'p5',
    name: 'Liam O\'Connor',
    age: 15,
    sex: 'M',
    triageLevel: 3,
    chiefComplaint: 'Ankle sprain',
    timeInEDMinutes: 50,
    location: 'Room 9',
    primaryPhysician: 'Dr. Smith',
    vitalsFlags: [],
    dispositionEstimate: 'Likely discharge',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 50).toISOString(), type: 'Arrived', description: 'Sports injury' }
    ],
    tasks: [
      { id: tid(7), description: 'XR ankle', ownerRole: 'Tech', dueInMinutes: -5, status: 'done', priority: 'low' }
    ]
  },
  {
    id: 'p6',
    name: 'Emily Wang',
    age: 54,
    sex: 'F',
    triageLevel: 1,
    chiefComplaint: 'Severe chest pain',
    timeInEDMinutes: 30,
    location: 'Resuscitation',
    primaryPhysician: 'Dr. Smith',
    vitalsFlags: ['tachycardic', 'hypotensive'],
    dispositionEstimate: 'Likely admit',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), type: 'Arrived', description: 'Acute chest pain, EMS' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(), type: 'ECG', description: 'ECG performed, ST changes' }
    ],
    tasks: [
      { id: tid(8), description: 'Activate cath lab', ownerRole: 'MD', dueInMinutes: -2, status: 'in_progress', priority: 'high' },
      { id: tid(9), description: 'Give ASA 325 mg', ownerRole: 'RN', dueInMinutes: 5, status: 'pending', priority: 'high' }
    ]
  },
  {
    id: 'p7',
    name: 'Olivia Brown',
    age: 38,
    sex: 'F',
    triageLevel: 4,
    chiefComplaint: 'Migraine',
    timeInEDMinutes: 110,
    location: 'Room 5',
    primaryPhysician: 'Dr. Lee',
    vitalsFlags: [],
    dispositionEstimate: 'Likely discharge',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 110).toISOString(), type: 'Arrived', description: 'Severe headache' }
    ],
    tasks: [
      { id: tid(10), description: 'Give antiemetic', ownerRole: 'RN', dueInMinutes: -30, status: 'done', priority: 'low' }
    ]
  },
  {
    id: 'p8',
    name: 'Noah Patel',
    age: 72,
    sex: 'M',
    triageLevel: 3,
    chiefComplaint: 'Fever and cough',
    timeInEDMinutes: 240,
    location: 'Room 2',
    primaryPhysician: 'Dr. Kim',
    vitalsFlags: ['febrile'],
    dispositionEstimate: 'Observation vs admit',
    events: [
      { timestamp: new Date(Date.now() - 1000 * 60 * 240).toISOString(), type: 'Arrived', description: 'Progressive cough' },
      { timestamp: new Date(Date.now() - 1000 * 60 * 200).toISOString(), type: 'CXR', description: 'CXR pending' }
    ],
    tasks: [
      { id: tid(11), description: 'Chest x-ray', ownerRole: 'Tech', dueInMinutes: 30, status: 'pending', priority: 'medium' }
    ]
  }
]

export default patients
