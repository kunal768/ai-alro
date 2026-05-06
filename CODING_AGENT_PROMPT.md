# Bay Area Real-Time Map Upgrade Prompt

Use this prompt exactly:

Implement a map-first simulation UX in this repo with persistent visualization and Bay Area data migration.

Requirements:
1) Add a permanent real-time map background that stays mounted for the full app lifecycle (scenario selection, intake, deliberation, resolution). All simulation visuals must render on top of this map.
2) Render and continuously update all geography layers: dasher locations, warehouses, delivery destinations, candidate routes, selected route, and final route. Use ghost/persistent layers so nothing disappears during playback.
3) Slow down playback for readability. Convert phase-driven hide/show behavior into additive reveal behavior: once a signal, route, or reasoning artifact appears, it remains visible through the end of simulation.
4) Migrate all London-centric seed/demo/mock data and prompts to Bay Area equivalents (SF, East Bay, South Bay, Peninsula, North Bay or similar). Update backend and frontend fixtures consistently.
5) Make the reasoning section readable: render structured headings/sections/lists/highlights rather than plain paragraph dumping.
6) Keep reasoner conclusion parsing contract intact (DECISION / RECOMMENDED_OPTION / FLAGS / OVERRIDE_REASON) so existing resolution logic still works.

Primary files to modify:
- frontend/src/App.jsx
- frontend/src/hooks/useDeliberation.js
- frontend/src/components/Phase2_Deliberation.jsx
- frontend/src/index.css
- backend/erp_service/seed_data.py
- backend/shared/utils.py
- backend/reasoner_agent/demo_scenarios.py
- backend/reasoner_agent/prompts.py
- backend/optimizer_agent/main.py (if geography constants are London-tuned)
- frontend/src/mockData.js
- frontend/src/scenarios.js
- backend/test_intake.py
- backend/test_reasoner.py

Implementation guidance:
- Create a dedicated map overlay component (e.g., frontend/src/components/RouteMap.jsx) and keep it always mounted from App shell.
- Use existing coordinate fields from signals/optimizer/resolution payloads for marker and route rendering.
- Preserve prior route/signal states in UI state so revealed items are never removed.
- Keep styling readable with clear layering, contrast, and section hierarchy.

Acceptance criteria:
- Permanent map in background at all times.
- Real-time updates for dasher + routes + delivery locations.
- Nothing disappears during simulation.
- Bay Area geography everywhere (seed/demo/mock/test data).
- Reasoning section is clearly readable and structured.
- No regression in final resolution parsing.
