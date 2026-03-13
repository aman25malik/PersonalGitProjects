# ED Command Center — Demo (Vite + React + TypeScript)

This is a local, demo prototype of an Emergency Department (ED) Command Center. It uses mock data only and simulates simple AI features on the frontend (no external APIs, no PHI).

Quick start

1. Install dependencies

```bash
npm install
```

2. Start development server

```bash
npm run dev
```

3. Open the app in your browser:

http://localhost:5173

What I added

- Source: `src/`
- Main entry: `src/main.tsx`
- App shell: `src/App.tsx`
- Components: `src/components/CommandBoard.tsx`, `src/components/PatientDetail.tsx`, `src/components/TaskList.tsx`, `src/components/HandoffAssistant.tsx`
- Mock data: `src/data/mockData.ts`
- Fake AI logic: `src/lib/aiSim.ts`
- Types: `src/types.ts`
- Styles: `src/styles/index.css`

Notes

- Data is fake and included in `src/data/mockData.ts` (8 patients).
- The "AI" layer in `src/lib/aiSim.ts` implements deterministic heuristics for risk, summaries, and handoffs.
- Tasks are editable and update the UI state only (no persistence).

Tailwind vs simple CSS — short guidance

- Tailwind CSS pros:
  - Rapid, consistent utility classes and responsive helpers.
  - Easier to iterate on UI prototypes at scale and enforce consistent spacing/colors.
  - Good if you expect to expand the UI and want standardized utilities.

- Simple CSS pros (what this demo uses):
  - Lower setup friction (no PostCSS/Tailwind install/config).
  - Easier to read for small demos and for developers who prefer authoring styles traditionally.

- Recommendation: keep the simple CSS for this small demo. Switch to Tailwind if you plan to rapidly expand the UI, reuse design tokens across many screens, or prefer utility-first styling.

If you want, I can:

- Convert the project to Tailwind (I will add config + classes and update styles). 
- Add a small `README` to the components describing props and key behaviors. 
