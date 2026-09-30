# 🚚 Supplychainer

### AI-Powered Multimodal Supply Chain Route Intelligence & Disruption-Aware Planning

Supplychainer is an intelligent supply-chain decision platform that combines **multimodal route optimization, disruption scenario modeling, threat intelligence, machine-learning delay prediction, supplier intelligence, and route history** into a single operational dashboard.

The system evaluates transportation networks across **road, rail, sea, and air**, dynamically incorporates disruption risk and predicted delays, and generates route recommendations based on different operational objectives.

---

## 🎯 What Problem Does Supplychainer Solve?

Modern supply chains are affected by:

* Geopolitical disruptions
* Port and airport congestion
* Infrastructure failures
* Weather-related disruptions
* Strikes and operational shutdowns
* Transportation delays
* Supplier reliability issues
* Changing transportation costs

Traditional route planners primarily optimize for distance, time, or cost.

Supplychainer instead treats routing as a **dynamic risk-aware decision problem**.

A route is evaluated using:

```text
Travel Time
     +
Predicted Disruption Delay
     +
Threat / Risk
     +
Transportation Cost
     ↓
Route Decision
```

The system can therefore compare alternative multimodal routes instead of simply selecting the shortest geographical path.

---

# 🧠 Core Capabilities

## 1. 🌐 Multimodal Route Optimization

Supplychainer represents the logistics network as a directed **NetworkX graph**.

Supported transportation modes include:

* 🚚 Road
* 🚆 Rail
* 🚢 Sea
* ✈️ Air

Transportation-mode nodes are connected through transfer edges, allowing the system to construct multimodal journeys.

Example:

```text
Origin
  │
  ▼
🚚 Road
  │
  ▼
🚢 Sea
  │
  ▼
🚆 Rail
  │
  ▼
Destination
```

The network is constructed from canonical logistics hubs and transportation connections.

---

# 🧭 Route Recommendation Engine

Supplychainer generates three operational routing strategies.

### ⚡ FASTEST

Prioritizes travel time while incorporating predicted disruption delays.

Conceptually:

```text
Route Weight =
Travel Time + Disruption Delay
```

---

### 🛡️ SAFEST

Penalizes routes exposed to higher threat levels.

Conceptually:

```text
Route Weight =
(Time + Delay) × Risk Penalty
```

---

### ⚖️ BALANCED

Balances transportation time, cost, and risk.

The current routing formulation uses:

```text
Balanced Weight =
    0.3 × Time
  + 0.5 × Cost
  + 0.2 × Risk
```

Each routing strategy is evaluated independently using **Dijkstra's shortest-path algorithm**.

---

# 🤖 Machine-Learning Delay Prediction

The intelligence layer contains a **Gradient Boosting quantile regression model** for operational delay prediction.

The model uses supply-chain features including:

* Leg type
* Origin node
* Destination node
* Transportation mode
* Condition flag
* NLP-derived severity information

Categorical variables are encoded using `LabelEncoder`.

The current production routing pipeline uses the **P85 quantile prediction** as its risk-aware delay signal.

P85 is used because the routing engine needs a more conservative delay estimate than a simple average or point estimate.

```text
Input Features
      │
      ▼
ML Quantile Model
      │
      ▼
Predicted Delay
      │
      ▼
Calibration Layer
      │
      ▼
Route Risk / ETA
```

The model artifacts are stored under:

```text
Execution/
├── risk_model.pkl
├── label_encoders.pkl
└── calibration_profiles.json
```

---

# ⚠️ Statistical Calibration

Raw machine-learning predictions are passed through a calibration layer.

The calibration profiles provide operational bounds derived from historical delay distributions.

The system applies:

```text
Raw ML Prediction
       │
       ▼
Historical Calibration
       │
       ├── Lower operational floor
       │
       └── Upper operational cap
       │
       ▼
Calibrated Delay
```

This prevents unrealistic model outputs from dominating route optimization.

---

# 🌪️ Disruption Scenario Engine

Supplychainer supports deterministic disruption scenarios through the `ScenarioManager`.

A scenario can affect:

* Threat level
* Expected delay
* Affected logistics hubs
* Route conditions
* Transportation operations

Conceptually:

```text
Disruption Scenario
        │
        ▼
Affected Hub
        │
   ┌────┴────┐
   ▼         ▼
Threat     Delay
   │         │
   └────┬────┘
        ▼
Dynamic Route Weight
        │
        ▼
Re-routing
```

This allows the same shipment to be evaluated under different operational conditions.

---

# 📰 Threat Intelligence & NLP

Supplychainer contains an NLP-based threat intelligence subsystem.

The intelligence pipeline is structured as:

```text
News / Text
     │
     ▼
News Ingestion
     │
     ▼
NLP Semantic Analysis
     │
     ▼
CARF Relevance Filtering
     │
     ▼
Threat Signal
     │
     ▼
Routing Engine
```

The NLP engine uses semantic similarity to identify disruption-related information.

The system also uses **CARF — Context-Aware Relevance Filtering** — to prevent irrelevant disruption signals from affecting unrelated transportation modes.

For example:

```text
Airport disruption
       ↓
Air transportation
       ✓ Relevant

Airport disruption
       ↓
Sea transportation
       ✗ Filtered
```

---

# 📡 Dynamic News Ingestion

The news ingestion subsystem retrieves operational intelligence through **Google News RSS**.

It supports:

* Location-aware queries
* Transportation-mode-aware queries
* Cached results
* Network timeout protection
* Offline fallback information

News is cached for a short period to avoid repeatedly requesting the same information.

If external news retrieval fails, the system falls back to predefined operational conditions so that route planning can continue.

---

# 🏭 Supplier Intelligence

Supplychainer includes a supplier intelligence module.

Supplier information is stored in:

```text
backend/data/suppliers.json
```

The supplier scoring pipeline evaluates factors including:

* Cost
* Lead time
* Reliability
* Disruption exposure

Conceptually:

```text
Supplier Data
     │
     ▼
Supplier Scorer
     │
 ┌───┼──────────────┐
 ▼   ▼              ▼
Cost Lead Time   Reliability
     │              │
     └──────┬───────┘
            ▼
     Disruption Risk
            │
            ▼
   Procurement Insight
```

---

# 🗺️ Canonical Hub Registry

Supplychainer uses a canonical logistics-hub registry instead of relying exclusively on free-form location strings.

The registry contains real-world logistics nodes such as:

* Ports
* Airports
* Rail hubs
* Road/logistics hubs

The backend provides hub lookup and search APIs so that frontend users can resolve locations to canonical network nodes.

This improves consistency between:

```text
User Input
    ↓
Hub Resolution
    ↓
Canonical Hub
    ↓
Network Node
    ↓
Route Optimization
```

---

# 💰 Currency Conversion

Route optimization is performed internally using **USD**.

The frontend can display route costs in supported currencies.

The currency layer separates:

```text
Internal Optimization Currency
              ↓
             USD
              ↓
      Currency Conversion
              ↓
       Display Currency
```

Supported display currencies include configurations such as:

* USD
* INR
* EUR
* GBP
* AED
* CNY

The exchange rates are configuration/demo rates rather than a live foreign-exchange market feed.

---

# 🕘 Route History

The frontend stores successful route decisions in Route History.

A saved history entry contains information such as:

* Origin
* Destination
* Transportation preference
* Routing policy
* Cargo type
* Priority
* Currency
* Active scenario
* Generated recommendations
* Creation timestamp

This allows users to return to previous route decisions and restore them in the route planner.

---

# 🖥️ Frontend

The frontend is built using:

* React 18
* Vite
* JavaScript/JSX
* Lucide icons

The main frontend modules include:

```text
frontend/src/
│
├── App.jsx
├── RouteRecommender.jsx
├── SupplierIntelligence.jsx
├── RouteHistory.jsx
├── BenchmarkCharts.jsx
└── components/
```

### Route Recommender

The main planning interface allows users to configure:

* Origin
* Destination
* Transport preference
* Routing policy
* Operational scenario
* Cargo type
* Priority
* Display currency

The frontend communicates with the FastAPI backend through REST APIs.

---

# 🔌 Backend

The backend is built with **FastAPI**.

The main application entry point is:

```text
backend/main.py
```

The backend initializes the core intelligence and routing components:

```text
FastAPI
  │
  ├── Node Resolver
  ├── Multimodal Network
  ├── Threat Intelligence
  ├── Scenario Manager
  ├── Route Recommender
  ├── Supplier Scorer
  ├── Currency Layer
  └── Simulator
```

---

# 🔗 API Endpoints

The backend exposes several API groups.

### Route Recommendations

```http
POST /api/recommend
```

Generates route recommendations based on the requested source, destination, transportation preference, routing policy, cargo, priority, scenario, and currency.

---

### Scenarios

```http
GET /api/scenarios
```

Returns available disruption scenarios.

---

### Currencies

```http
GET /api/currencies
```

Returns supported display currencies and their configured exchange rates.

---

### Hubs

```http
GET /api/hubs
```

Returns the canonical logistics-hub registry.

---

### Hub Search

```http
GET /api/hubs/search?q=<query>
```

Searches hubs by:

* Display name
* Alias
* Country
* Hub ID

---

### Network

```http
GET /api/network
```

Returns the current multimodal network representation.

---

### System Status

```http
GET /api/status
```

Returns operational information such as:

* ML status
* Active trips
* Simulation tick
* Geographic scope
* Hub count

---

### WebSocket

```text
/ws
```

Provides live backend engine status to the frontend.

The status channel can communicate information such as:

```text
WARMING RISK ENGINE
        ↓
FULLY OPERATIONAL
```

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────────────┐
                         │       React + Vite           │
                         │          Frontend            │
                         │                              │
                         │  Route Recommender           │
                         │  Supplier Intelligence       │
                         │  Route History               │
                         │  Benchmark Charts             │
                         │  System Console               │
                         └──────────────┬───────────────┘
                                        │
                               REST API / WebSocket
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │        FastAPI Backend        │
                         │                              │
                         │       backend/main.py         │
                         └──────────────┬───────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
             Node Resolver       Scenario Manager    Threat Intelligence
                    │                   │                   │
                    ▼                   ▼                   ▼
             Canonical Hubs      Disruption Data       NLP / CARF
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
                              Multimodal Network
                                        │
                                        ▼
                               Route Recommender
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                           FASTEST    SAFEST   BALANCED
                              │         │         │
                              └─────────┼─────────┘
                                        ▼
                                    Dijkstra
                                        │
                                        ▼
                               Route Evaluation
                                        │
                              ┌─────────┼─────────┐
                              ▼         ▼         ▼
                             ETA       Cost       Risk
                              │         │         │
                              └─────────┼─────────┘
                                        ▼
                                Recommendations
                                        │
                                        ▼
                                React Frontend
```

---

# 🔄 End-to-End Routing Pipeline

A route recommendation follows this process:

```text
1. User enters origin and destination
              ↓
2. Frontend sends /api/recommend
              ↓
3. Node Resolver resolves canonical hubs
              ↓
4. Multimodal Network provides possible paths
              ↓
5. Scenario Manager activates disruption conditions
              ↓
6. Threat Intelligence evaluates operational risk
              ↓
7. ML model predicts disruption delay
              ↓
8. Calibration constrains the prediction
              ↓
9. Dynamic edge weights are calculated
              ↓
10. FASTEST / SAFEST / BALANCED routing runs
              ↓
11. Dijkstra finds candidate paths
              ↓
12. Cost, time and risk are evaluated
              ↓
13. Route recommendations are returned
              ↓
14. Frontend displays the results
              ↓
15. Successful route decision is stored in history
```

---

# 🧩 Project Structure

```text
supply_chainer/
│
├── backend/
│   ├── main.py
│   │
│   ├── engine/
│   │   ├── route_recommender.py
│   │   ├── multimodal_network.py
│   │   ├── node_resolver.py
│   │   ├── threat_intelligence.py
│   │   ├── news_ingestion.py
│   │   ├── scenario_manager.py
│   │   ├── supplier_scorer.py
│   │   ├── currency.py
│   │   │
│   │   ├── graph_model.py
│   │   ├── simulator.py
│   │   ├── baseline.py
│   │   └── weather_integration.py
│   │
│   └── data/
│       ├── canonical_hubs.json
│       ├── canonical_locations.json
│       └── suppliers.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── RouteRecommender.jsx
│   │   ├── SupplierIntelligence.jsx
│   │   ├── RouteHistory.jsx
│   │   ├── BenchmarkCharts.jsx
│   │   └── components/
│   │
│   ├── package.json
│   └── vite.config.js
│
├── Execution/
│   ├── risk_model.pkl
│   ├── label_encoders.pkl
│   ├── nlp_anchors.pt
│   ├── calibration_profiles.json
│   └── api.py
│
├── Code/
│   └── Training / modelling utilities
│
├── benchmarks/
│   └── Benchmarking and evaluation artifacts
│
└── scratch/
    └── Development / experimental files
```

---

# 🛠️ Technology Stack

## Frontend

| Technology   | Purpose                   |
| ------------ | ------------------------- |
| React 18     | Frontend application      |
| Vite         | Development/build tooling |
| JSX          | UI components             |
| Lucide React | Interface icons           |

## Backend

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| Python     | Core backend language        |
| FastAPI    | REST API                     |
| WebSockets | Live engine status           |
| NetworkX   | Multimodal graph and routing |
| Pydantic   | API request validation       |

## Machine Learning / Intelligence

| Technology            | Purpose                           |
| --------------------- | --------------------------------- |
| scikit-learn          | Quantile regression               |
| Gradient Boosting     | Delay prediction                  |
| joblib                | Model serialization               |
| PyTorch               | NLP artifact handling             |
| Sentence Transformers | Semantic threat analysis          |
| CARF                  | Context-aware relevance filtering |

## Data / Intelligence

| Component              | Purpose                    |
| ---------------------- | -------------------------- |
| Canonical Hub Registry | Logistics-node resolution  |
| Scenario Manager       | Deterministic disruptions  |
| Google News RSS        | Operational news ingestion |
| Supplier Dataset       | Supplier intelligence      |
| Calibration Profiles   | Delay-bound calibration    |

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/kamran-bisati/supply_chainer.git
cd supply_chainer
```

---

# 🐍 Backend Setup

Create and activate a Python virtual environment.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the FastAPI backend from the project root using the project's configured backend entry point.

The backend runs on:

```text
http://localhost:8000
```

FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

---

# ⚛️ Frontend Setup

Move into the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend is normally available at:

```text
http://localhost:5173
```

The Vite frontend communicates with the FastAPI backend through:

```text
/api → FastAPI
/ws  → FastAPI WebSocket
```

---

# 🧪 Typical Usage

### Step 1 — Select Origin

Choose a canonical logistics hub.

### Step 2 — Select Destination

Choose the destination hub.

### Step 3 — Select Transport Preference

Choose:

```text
Any
Road
Rail
Sea
Air
```

### Step 4 — Select Routing Strategy

Choose:

```text
FASTEST
SAFEST
BALANCED
```

### Step 5 — Select Operational Scenario

Run the route under normal or disrupted conditions.

### Step 6 — Generate Recommendations

Supplychainer evaluates the network and returns route alternatives.

### Step 7 — Compare

Review:

* Travel time
* Predicted delay
* Cost
* Threat/risk
* Transportation modes
* Route legs
* Scenario effects

### Step 8 — Restore Historical Routes

Previously generated recommendations can be accessed through Route History.

---

# 🔬 Design Philosophy

Supplychainer separates the system into independent intelligence layers.

```text
DATA
 ↓
NETWORK
 ↓
INTELLIGENCE
 ↓
PREDICTION
 ↓
OPTIMIZATION
 ↓
DECISION
 ↓
VISUALIZATION
```

This makes it possible to improve one component without redesigning the entire platform.

For example:

```text
New News Source
      ↓
Threat Intelligence
      ↓
Risk Signal
      ↓
Existing Routing Engine
```

or:

```text
Improved ML Model
      ↓
Better Delay Estimate
      ↓
Existing Route Optimizer
```

---

# 🧠 Why Multimodal Routing?

A real logistics journey rarely consists of a single transportation mode.

For example:

```text
Factory
  │
  ▼
Truck
  │
  ▼
Port
  │
  ▼
Ship
  │
  ▼
Rail Terminal
  │
  ▼
Train
  │
  ▼
Final Distribution Hub
```

Supplychainer models these transitions explicitly through transportation and transfer edges.

This allows the route optimizer to evaluate different combinations rather than only comparing direct routes.

---

# 🛡️ Reliability & Fallback Design

The system contains fallback mechanisms so that core route planning can continue when external intelligence or model artifacts are unavailable.

Examples include:

### News fallback

If external RSS ingestion fails:

```text
Live News
   ↓
Unavailable
   ↓
Operational Fallback
```

### ML fallback

If production model artifacts are unavailable, the predictor can use deterministic operational priors.

This prevents a missing model artifact from completely disabling the routing engine.

---

# 📊 Benchmarking & Supporting Systems

The project also contains simulation and benchmarking components.

Supporting backend components include:

```text
graph_model.py
simulator.py
baseline.py
weather_integration.py
```

These components support:

* Logistics simulation
* Weather integration
* Traffic/backlog modeling
* Baseline routing
* Synthetic trip generation
* Benchmarking

They coexist with the newer canonical-hub multimodal routing architecture.

---

# 🔐 Operational Scope

Supplychainer is designed as a **decision-support system**.

Its outputs represent model-based and scenario-based operational estimates.

Important distinctions:

* ML predictions are estimates, not guarantees.
* Scenario delays represent modeled disruption conditions.
* News-derived signals depend on available external information.
* Currency conversion uses configured rates.
* Route recommendations depend on the selected routing policy and current network state.

---

# 📌 Current Architecture Summary

```text
                 SUPPLYCHAINER
                      │
       ┌──────────────┴──────────────┐
       │                             │
   FRONTEND                       BACKEND
       │                             │
   React/Vite                    FastAPI
       │                             │
       │                     ┌───────┴────────┐
       │                     │                │
       │                Intelligence      Routing
       │                     │                │
       │               ┌─────┴─────┐          │
       │               │           │          │
       │              NLP         ML      Multimodal
       │               │           │        Network
       │               │           │          │
       │              CARF    Delay Model   Dijkstra
       │               │           │          │
       │               └─────┬─────┘          │
       │                     │                │
       │                     └───────┬────────┘
       │                             │
       └─────────────────────────────┤
                                     ▼
                              Route Decisions
                                     │
                              ┌──────┼──────┐
                              ▼      ▼      ▼
                             ETA    COST    RISK
                                     │
                                     ▼
                              User Dashboard
```

---

# 🚧 Future Development

The architecture is designed to support further extensions such as:

* Multi-quantile delay bands
* Additional threat-type classification
* More external intelligence sources
* Improved historical calibration
* Additional transportation networks
* Real-time operational data feeds
* More advanced route optimization
* Expanded supplier intelligence
* More detailed route analytics

---

# 👥 Project

**Supplychainer** is a hackathon-built intelligent supply-chain routing and risk-analysis platform.

Repository:

[Supplychainer on GitHub](https://github.com/kamran-bisati/supply_chainer?utm_source=chatgpt.com)

---

## License

Add the project's applicable license here if a license file is present in the repository.
