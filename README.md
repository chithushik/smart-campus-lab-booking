# Smart Campus Lab Equipment Booking

A multi-agent simulation for booking shared university lab equipment, using an OWL ontology to enforce rules.

## What it does

Student agents request lab equipment. A Lab Manager agent checks an RDF/OWL ontology and approves or denies each request based on six rules.

## Features

- **Agent-based simulation** — StudentAgent makes requests, LabManagerAgent validates them. Agents run in random order.
- **OWL/RDF ontology** — All facts about equipment, students, certifications, and reservations live in `lab_ontology.ttl`.
- **Six-rule validation** — Every request is checked against six rules before approval.
- **Dynamic state** — Approved bookings add a Reservation triple to the graph, so later conflicts are detected automatically.
- **Streamlit UI** — Navy blue / white / black interface with four tabs: Dashboard, Equipment Catalog, Make a Request, Simulation Results.
- **Metrics and audit** — Approval rate, detailed results table, raw manager log, and list of reservations added.
- **Extensible** — Same design works for hospital rooms, EV chargers, or drone landing slots.

## The Six Rules

1. Equipment must exist in the ontology.
2. Equipment must not be under maintenance.
3. Equipment must be marked available.
4. Student must hold the required certification.
5. Requested duration must not exceed the equipment's maximum.
6. The time slot must not already be booked for that equipment.

If all six rules pass, a Reservation is added to the ontology.

## Agents

- `StudentAgent` — requests equipment.
- `LabManagerAgent` — validates requests against the ontology.

## Files

- `app.py` — Streamlit app with agents and UI.
- `lab_ontology.ttl` — OWL ontology with equipment, students, and rules.
- `simulation_notebook.ipynb` — Jupyter notebook version of the simulation.

## How to run

pip install mesa rdflib streamlit pandas , 
streamlit run app.py


Open your browser at http://localhost:8501.

## UI

- Dashboard — overview and rules
- Equipment Catalog — live list of equipment from the ontology
- Make a Request — pick a student, equipment, time slot, and duration
- Simulation Results — run a batch of 7 requests and see outcomes

## Sample results

| Student  | Equipment     | Slot  | Outcome    | Reason                                      |
|----------|---------------|-------|------------|---------------------------------------------|
| Student1 | LaserCutter1  | Mon10 | APPROVED   | All rules passed                            |
| Student2 | LaserCutter1  | Mon11 | DENIED     | Missing required certification: LaserSafety |
| Student2 | ChemAnalyzer1 | Mon10 | APPROVED   | All rules passed                            |
| Student3 | Oscilloscope1 | Tue14 | APPROVED   | All rules passed                            |
| Student1 | 3DPrinter1    | Tue14 | DENIED     | Equipment is under maintenance              |
| Student5 | Centrifuge1   | Wed09 | DENIED     | Duration 10h exceeds max 2.0h               |
| Student1 | LaserCutter1  | Mon10 | DENIED     | Time slot Mon10 already booked              |

## Tech

- Mesa — agent-based modeling
- RDFLib — RDF/OWL in Python
- Streamlit — web UI
- pandas — tables

## Author

Chithushik — Smart Campus assignment, 2025

## Screenshots

<img width="1872" height="857" alt="D1" src="https://github.com/user-attachments/assets/9e3da897-8336-4065-9728-6fa4e13666e2" />

<img width="1858" height="858" alt="D2" src="https://github.com/user-attachments/assets/d3b56ee6-94e1-47dc-a374-a0e76890acf9" />

<img width="1867" height="851" alt="D3" src="https://github.com/user-attachments/assets/0646844a-50c3-45c7-94d9-18fd1aa39d7b" />

<img width="1855" height="872" alt="D4" src="https://github.com/user-attachments/assets/40d9b73d-98be-408f-8180-fecdc8c02236" />

<img width="1853" height="857" alt="D5" src="https://github.com/user-attachments/assets/c132b3b3-8e9d-4b8d-8307-b6cbcdc80090" />











