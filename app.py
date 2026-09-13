# app.py - Streamlit UI for Smart Campus Lab Equipment Booking
import streamlit as st
import pandas as pd
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD

# ---------------- AGENT CODE (copied from notebook) ----------------
from mesa import Agent, Model

NS = Namespace("http://example.org/lab.owl#")


class StudentAgent(Agent):
    def __init__(self, model, unique_id, student_uri, equipment_name, time_slot, duration_hours):
        super().__init__(model)
        self.unique_id = unique_id
        self.student_uri = student_uri
        self.equipment_name = equipment_name
        self.time_slot = time_slot
        self.duration_hours = duration_hours
        self.result = None

    def step(self):
        self.result = self.model.lab_manager.process_request(self)


class LabManagerAgent(Agent):
    def __init__(self, model, unique_id, graph):
        super().__init__(model)
        self.unique_id = unique_id
        self.graph = graph
        self.reservation_counter = 0
        self.log = []

    def step(self):
        pass

    def process_request(self, student):
        eq_uri = NS[student.equipment_name]
        stu_uri = student.student_uri

        if (eq_uri, RDF.type, NS.Equipment) not in self.graph:
            return self._deny(student, "Equipment not found in ontology")

        for m in self.graph.objects(eq_uri, NS.underMaintenance):
            if m == Literal(True, datatype=XSD.boolean):
                return self._deny(student, "Equipment is under maintenance")

        for a in self.graph.objects(eq_uri, NS.isAvailable):
            if a != Literal(True, datatype=XSD.boolean):
                return self._deny(student, "Equipment is not available")

        required_certs = list(self.graph.objects(eq_uri, NS.requiresCertification))
        if required_certs:
            student_certs = list(self.graph.objects(stu_uri, NS.hasCertification))
            if not any(cert in student_certs for cert in required_certs):
                cert_names = ", ".join(str(c).split("#")[-1] for c in required_certs)
                return self._deny(student, f"Missing required certification: {cert_names}")

        max_dur = list(self.graph.objects(eq_uri, NS.maxDurationHours))
        if max_dur:
            limit = float(max_dur[0])
            if student.duration_hours > limit:
                return self._deny(student, f"Duration {student.duration_hours}h exceeds max {limit}h")

        for res in self.graph.subjects(NS.reserves, eq_uri):
            for slot in self.graph.objects(res, NS.timeSlot):
                if str(slot) == student.time_slot:
                    return self._deny(student, f"Time slot {student.time_slot} already booked")

        self.reservation_counter += 1
        res_uri = NS[f"Reservation{self.reservation_counter}"]
        self.graph.add((res_uri, RDF.type, NS.Reservation))
        self.graph.add((res_uri, NS.reserves, eq_uri))
        self.graph.add((res_uri, NS.reservedBy, stu_uri))
        self.graph.add((res_uri, NS.timeSlot, Literal(student.time_slot)))

        return self._approve(student, res_uri)

    def _approve(self, student, res_uri):
        msg = f"APPROVED {student.equipment_name} @ {student.time_slot}"
        self.log.append((student.unique_id, student.equipment_name, student.time_slot, "APPROVED"))
        return msg

    def _deny(self, student, reason):
        msg = f"DENIED {student.equipment_name} @ {student.time_slot} -> {reason}"
        self.log.append((student.unique_id, student.equipment_name, student.time_slot, f"DENIED: {reason}"))
        return msg


class LabBookingModel(Model):
    def __init__(self, requests):
        super().__init__()
        self.graph = Graph()
        self.graph.parse("lab_ontology.ttl", format="turtle")
        self.lab_manager = LabManagerAgent(self, unique_id=1, graph=self.graph)
        self.students = []
        for i, (stu, eq, slot, dur) in enumerate(requests):
            agent = StudentAgent(
                model=self,
                unique_id=i + 2,
                student_uri=NS[stu],
                equipment_name=eq,
                time_slot=slot,
                duration_hours=dur,
            )
            self.students.append(agent)

    def step(self):
        self.agents.shuffle_do("step")

    def run_all(self):
        self.step()


# ---------------- HELPER: read ontology into friendly lists ----------------
@st.cache_data
def read_ontology():
    g = Graph()
    g.parse("lab_ontology.ttl", format="turtle")

    equipment = sorted(str(u).split("#")[-1] for u in g.subjects(RDF.type, NS.Equipment))
    students = sorted(str(u).split("#")[-1] for u in g.subjects(RDF.type, NS.Student))
    if not students:
        students = ["Student1", "Student2", "Student3", "Student4", "Student5"]

    time_slots = ["Mon09", "Mon10", "Mon11", "Mon14", "Tue09", "Tue10", "Tue14", "Wed09", "Wed10", "Thu09"]

    student_certs = {}
    for s in students:
        stu_uri = NS[s]
        certs = [str(c).split("#")[-1] for c in g.objects(stu_uri, NS.hasCertification)]
        student_certs[s] = certs if certs else ["None"]

    equipment_max = {}
    for e in equipment:
        eq_uri = NS[e]
        max_dur = list(g.objects(eq_uri, NS.maxDurationHours))
        equipment_max[e] = int(float(max_dur[0])) if max_dur else 1

    return equipment, students, time_slots, student_certs, equipment_max


# ---------------- STREAMLIT THEME & LAYOUT ----------------

st.set_page_config(
    page_title="Smart Campus Lab Booking",
    page_icon="🔬",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0A192F; color: #FFFFFF; }
    h1, h2, h3, h4, h5, h6, p, label, div { color: #FFFFFF !important; }
    .main-title {
        background-color: #000000; padding: 20px; border-radius: 12px;
        border-left: 8px solid #FFFFFF; margin-bottom: 20px;
    }
    .main-title h1 { color: #FFFFFF; margin: 0; font-size: 36px; }
    .main-title p { color: #FFFFFF; margin: 5px 0 0 0; opacity: 0.8; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: #000000; padding: 8px; border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #0A192F; color: #FFFFFF; border-radius: 8px; padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important; color: #0A192F !important; font-weight: bold;
    }
    .stButton > button {
        background-color: #FFFFFF; color: #0A192F; font-weight: bold;
        border: 2px solid #000000; border-radius: 8px; padding: 8px 20px;
    }
    .stButton > button:hover {
        background-color: #000000; color: #FFFFFF; border: 2px solid #FFFFFF;
    }
    section[data-testid="stSidebar"] { background-color: #000000; }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .result-card {
        padding: 18px; border-radius: 12px; margin-top: 16px;
        border-left: 8px solid #FFFFFF; background-color: #000000;
    }
    .result-ok { border-left-color: #00C853; }
    .result-bad { border-left-color: #D50000; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-title">
        <h1>🔬 Smart Campus Lab Equipment Booking</h1>
        <p>Agent-based simulation + OWL ontology reasoning</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load ontology data once (needed for sidebar stats)
equipment_list, student_list, time_slots, student_certs, equipment_max = read_ontology()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    st.markdown("---")
    st.write("**Theme:** Navy / White / Black")
    st.write("**Engine:** Mesa + RDFLib")
    st.write("**Ontology:** lab_ontology.ttl")
    st.markdown("---")
    st.markdown("### 📌 Quick stats")
    st.write(f"- 🧰 Equipment: **{len(equipment_list)}**")
    st.write(f"- 👩‍🎓 Students: **{len(student_list)}**")
    st.write(f"- 📅 Time slots: **{len(time_slots)}**")
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption(
        "Multi-agent simulation where student agents request shared lab "
        "equipment and a mediator agent enforces ontology-based rules "
        "(certification, maintenance, duration, time-slot conflicts)."
    )
    st.markdown("---")
    st.caption("Built for Smart Campus assignment · 2025")

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Dashboard", "🧰 Equipment Catalog", "📝 Make a Request", "📊 Simulation Results"]
)

# ---------------- TAB 1: Dashboard ----------------
with tab1:
    st.markdown("### 🏠 Welcome")
    st.write(
        "This app simulates a **Smart Campus lab equipment booking system**. "
        "Students request equipment. A central **Lab Manager agent** checks the "
        "**OWL ontology** to enforce rules about certifications, maintenance, "
        "duration limits, and time-slot conflicts."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧰 Equipment", len(equipment_list))
    col2.metric("👩‍🎓 Students", len(student_list))
    col3.metric("📅 Time Slots", len(time_slots))
    col4.metric("🔒 Rules", 6)

    st.markdown("---")

    st.markdown("### 🔄 How it works")
    st.markdown(
        """
        1. A **Student agent** creates a request (equipment + time slot + duration).
        2. The **Lab Manager agent** queries the RDF/OWL ontology.
        3. Six rules are checked in order. The first failure denies the request.
        4. If all rules pass, a **Reservation** triple is added to the graph.
        5. Approved bookings block that time slot for later requests.
        """
    )

    st.markdown("### 🧠 Rules enforced by the Lab Manager")
    rules = [
        ("1️⃣ Existence", "Equipment must be declared in the ontology."),
        ("2️⃣ Maintenance", "Equipment must not be under maintenance."),
        ("3️⃣ Availability", "Equipment must be flagged available."),
        ("4️⃣ Certification", "Student must hold the required certification."),
        ("5️⃣ Duration", "Requested duration must not exceed the equipment's max."),
        ("6️⃣ Conflict", "Time slot must not already be reserved for that equipment."),
    ]
    for tag, desc in rules:
        st.markdown(f"**{tag}** — {desc}")

    st.markdown("---")
    st.markdown("### 🗺️ Architecture")
    st.code(
        """
  ┌──────────────────┐        request         ┌────────────────────┐
  │  StudentAgent    │ ─────────────────────► │  LabManagerAgent   │
  │  (many)          │                        │  (one mediator)    │
  └──────────────────┘                        └─────────┬──────────┘
                                                        │
                                                        │ SPARQL / graph
                                                        │ checks
                                                        ▼
                                              ┌────────────────────┐
                                              │  OWL Ontology      │
                                              │  (lab_ontology.ttl)│
                                              │  + Reservations    │
                                              └────────────────────┘
        """,
        language="text",
    )

# ---------------- TAB 2: Equipment Catalog ----------------
with tab2:
    st.markdown("### 🧰 Equipment Catalog")
    st.caption("Live view from the ontology (lab_ontology.ttl)")

    catalog_graph = Graph()
    catalog_graph.parse("lab_ontology.ttl", format="turtle")

    equipment_uris = list(catalog_graph.subjects(RDF.type, NS.Equipment))

    if not equipment_uris:
        st.warning("No equipment found in the ontology.")
    else:
        cols = st.columns(2)
        for idx, eq_uri in enumerate(sorted(equipment_uris, key=lambda u: str(u))):
            eq_name = str(eq_uri).split("#")[-1]

            avail = list(catalog_graph.objects(eq_uri, NS.isAvailable))
            avail = str(avail[0]) if avail else "unknown"

            maint = list(catalog_graph.objects(eq_uri, NS.underMaintenance))
            maint = str(maint[0]) if maint else "unknown"

            max_dur = list(catalog_graph.objects(eq_uri, NS.maxDurationHours))
            max_dur = str(max_dur[0]) if max_dur else "—"

            certs = list(catalog_graph.objects(eq_uri, NS.requiresCertification))
            cert_names = ", ".join(str(c).split("#")[-1] for c in certs) if certs else "None"

            if maint == "true":
                status = "🔧 Under Maintenance"
                status_color = "#FFB000"
            elif avail == "true":
                status = "✅ Available"
                status_color = "#00C853"
            else:
                status = "⛔ Not Available"
                status_color = "#D50000"

            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div style="background-color:#000000; padding:16px; border-radius:12px;
                                border-left:6px solid {status_color}; margin-bottom:14px;">
                        <h3 style="color:#FFFFFF; margin:0 0 6px 0;">🔬 {eq_name}</h3>
                        <p style="color:{status_color}; font-weight:bold; margin:0 0 8px 0;">{status}</p>
                        <p style="color:#FFFFFF; margin:2px 0;"><b>Max duration:</b> {max_dur} h</p>
                        <p style="color:#FFFFFF; margin:2px 0;"><b>Required certification:</b> {cert_names}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---------------- TAB 3: Make a Request ----------------
with tab3:
    st.markdown("### 📝 Make a Booking Request")
    st.caption("Pick a student, equipment, time slot and duration. The Lab Manager will decide.")

    col_a, col_b = st.columns(2)

    with col_a:
        selected_student = st.selectbox("👩‍🎓 Student", student_list)
        certs = student_certs.get(selected_student, ["None"])
        st.markdown(
            f"<p style='color:#FFB000;'><b>Certifications held:</b> {', '.join(certs)}</p>",
            unsafe_allow_html=True,
        )

        selected_equipment = st.selectbox("🧰 Equipment", equipment_list)

    with col_b:
        selected_slot = st.selectbox("📅 Time slot", time_slots)
        max_for_eq = equipment_max.get(selected_equipment, 1)
        duration = st.slider(
            "⏱️ Duration (hours)",
            min_value=1,
            max_value=10,
            value=min(2, max_for_eq),
        )
        st.caption(f"Max allowed for **{selected_equipment}** is **{max_for_eq} h**.")

    submit = st.button("🚀 Submit Request")

    if submit:
        model = LabBookingModel([(selected_student, selected_equipment, selected_slot, duration)])
        model.run_all()
        result = model.students[0].result

        if result.startswith("APPROVED"):
            st.markdown(
                f"""
                <div class="result-card result-ok">
                    <h3 style="color:#00C853; margin:0;">✅ APPROVED</h3>
                    <p style="margin:6px 0 0 0;">
                        <b>{selected_student}</b> got <b>{selected_equipment}</b>
                        for slot <b>{selected_slot}</b> ({duration} h).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.balloons()
        else:
            reason = result.split("->", 1)[-1].strip() if "->" in result else result
            st.markdown(
                f"""
                <div class="result-card result-bad">
                    <h3 style="color:#D50000; margin:0;">❌ DENIED</h3>
                    <p style="margin:6px 0 0 0;">
                        <b>{selected_student}</b> could not book <b>{selected_equipment}</b>
                        for slot <b>{selected_slot}</b>.
                    </p>
                    <p style="margin:6px 0 0 0;"><b>Reason:</b> {reason}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("🔎 See how the Lab Manager decided"):
            st.code(result, language="text")

# ---------------- TAB 4: Simulation Results ----------------
with tab4:
    st.markdown("### 📊 Full Simulation — Batch of 7 Requests")
    st.caption("Runs a mixed batch in one simulation round and shows every outcome.")

    default_batch = [
        ("Student1", "LaserCutter1",  "Mon10", 2),
        ("Student2", "LaserCutter1",  "Mon11", 2),
        ("Student2", "ChemAnalyzer1", "Mon10", 3),
        ("Student3", "Oscilloscope1", "Tue14", 1),
        ("Student1", "3DPrinter1",    "Tue14", 4),
        ("Student5", "Centrifuge1",   "Wed09", 10),
        ("Student1", "LaserCutter1",  "Mon10", 2),
    ]

    st.markdown("**Batch being simulated:**")
    batch_df = pd.DataFrame(
        default_batch,
        columns=["Student", "Equipment", "Time Slot", "Duration (h)"],
    )
    st.dataframe(batch_df, use_container_width=True, hide_index=True)

    run_batch = st.button("▶️ Run Batch Simulation")

    if run_batch:
        model = LabBookingModel(default_batch)
        model.run_all()

        rows = []
        for student in model.students:
            idx = student.unique_id - 2
            orig = default_batch[idx]
            raw = student.result or ""
            if raw.startswith("APPROVED"):
                status = "✅ APPROVED"
                reason = "All rules passed"
            else:
                status = "❌ DENIED"
                reason = raw.split("->", 1)[-1].strip() if "->" in raw else raw
            rows.append(
                {
                    "Student": orig[0],
                    "Equipment": orig[1],
                    "Time Slot": orig[2],
                    "Duration (h)": orig[3],
                    "Outcome": status,
                    "Reason": reason,
                }
            )

        result_df = pd.DataFrame(rows)

        approved = (result_df["Outcome"] == "✅ APPROVED").sum()
        denied = (result_df["Outcome"] == "❌ DENIED").sum()
        total = len(result_df)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Requests", total)
        m2.metric("✅ Approved", approved)
        m3.metric("❌ Denied", denied)
        m4.metric("Approval Rate", f"{(approved / total * 100):.0f}%")

        st.markdown("### 📋 Detailed Results")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        st.markdown("### 🔎 Raw Manager Log (order is random because agents act in random order)")
        log_df = pd.DataFrame(
            model.lab_manager.log,
            columns=["Student ID", "Equipment", "Time Slot", "Decision"],
        )
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        with st.expander("🧠 Reservations added to the ontology"):
            res_uris = list(model.graph.subjects(RDF.type, NS.Reservation))
            res_rows = []
            for r in res_uris:
                reserved_eq = next(iter(model.graph.objects(r, NS.reserves)), None)
                reserved_by = next(iter(model.graph.objects(r, NS.reservedBy)), None)
                slot = next(iter(model.graph.objects(r, NS.timeSlot)), None)
                res_rows.append(
                    {
                        "Reservation": str(r).split("#")[-1],
                        "Equipment": str(reserved_eq).split("#")[-1] if reserved_eq else "—",
                        "By": str(reserved_by).split("#")[-1] if reserved_by else "—",
                        "Time Slot": str(slot) if slot else "—",
                    }
                )
            if res_rows:
                st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No reservations were created.")
    else:
        st.info("Click **▶️ Run Batch Simulation** to see the full set of decisions.")