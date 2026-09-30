from fastapi import FastAPI, WebSocket, Query
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware

from .engine.graph_model import create_logistics_network
from .engine.simulator import LogisticsSimulator
from .engine.threat_intelligence import ThreatIntelligencePredictor
from .engine.baseline import BaselineRouter
from .engine.weather_integration import APIWeatherProvider
from .engine.multimodal_network import (
    create_multimodal_network,
    load_canonical_hubs
)
from .engine.route_recommender import RouteRecommender
from .engine.scenario_manager import ScenarioManager
from .engine.supplier_scorer import SupplierScorer
from .engine.currency import get_supported_currencies, normalize_currency


# Global Engine State
network = create_logistics_network()  # Still US-only simulator
simulator = LogisticsSimulator(
    network,
    weather_provider=APIWeatherProvider()
)

predictor = ThreatIntelligencePredictor()
baseline = BaselineRouter(network)


# Product layer (Supplychainer Architecture)
# Now using Canonical Hubs
multimodal_net = create_multimodal_network()
scenario_mgr = ScenarioManager()

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

recommender = RouteRecommender(
    multimodal_net,
    predictor,
    simulator,
    scenario_mgr,
    demo_mode=DEMO_MODE
)

canonical_hubs = load_canonical_hubs()

supplier_scorer = SupplierScorer(
    os.path.join(
        os.path.dirname(__file__),
        "data",
        "suppliers.json"
    )
)


class RecommendRequest(BaseModel):
    source: str
    destination: str
    cargo_type: str = "general"
    priority: str = "normal"
    budget_sensitivity: str = "medium"
    transport_preference: str = "any"
    routing_policy: str = "STRICT"
    scenario: Optional[str] = None
    overrides: Optional[dict] = None

    # New:
    # Currency used only for displaying calculated costs.
    # Route optimization continues to use USD internally.
    currency: str = "USD"


class SourcingRequest(BaseModel):
    category: str = "Electronics"
    current_inventory: int = 1000
    safety_stock: int = 1500
    demand_forecast: int = 800
    scenario: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Supplychainer Engine Active: Canonical Global Registry Loaded.")

    if not DEMO_MODE:
        asyncio.create_task(
            asyncio.to_thread(
                recommender.run_background_warmup
            )
        )

    yield


app = FastAPI(
    title="Smart Supply Chain API",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/scenarios")
def get_scenarios():
    """Returns available disruption scenarios."""
    return scenario_mgr.get_all_scenarios()


@app.get("/api/currencies")
def get_currencies():
    """
    Returns currencies supported by the Executive Dashboard.

    Exchange rates are expressed as:
        1 USD = exchange_rate units of target currency
    """
    currencies = get_supported_currencies()

    return {
        "base_currency": "USD",
        "currencies": currencies
    }


@app.get("/api/hubs")
def get_hubs():
    """Returns the full canonical hub registry."""
    return canonical_hubs


@app.get("/api/hubs/search")
def search_hubs(q: str = Query(..., min_length=1)):
    """Search hubs by display_name, aliases, or country."""
    q = q.lower()

    results = []

    for hub in canonical_hubs:
        if (
            q in hub["display_name"].lower()
            or any(q in a.lower() for a in hub["aliases"])
            or q in hub["country"].lower()
            or q in hub["id"].lower()
        ):
            results.append(hub)

    return results


@app.get("/api/network")
def get_network():
    nodes = []

    for n, data in multimodal_net.nodes(data=True):
        nodes.append({
            "id": n,
            "display_name": data.get("display_name"),
            "type": data.get("type")
        })

    edges = []
    seen = set()

    for u, v, data in multimodal_net.edges(data=True):
        edge_key = tuple(sorted((u, v)))

        if edge_key not in seen:
            edges.append({
                "source": u,
                "target": v,
                "baseline_time": data.get("baseline_time")
            })
            seen.add(edge_key)

    return {
        "nodes": nodes,
        "edges": edges
    }


@app.get("/api/status")
def get_status():
    return {
        "ml_trained": True,
        "active_trips": len(simulator.active_trips),
        "tick": simulator.time_tick,
        "is_supplychainer": True,
        "geo_scope": "Global (Canonical)",
        "hub_count": len(canonical_hubs)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            if recommender.warmup_failed:
                status_msg = "WARM-UP FAILED"
            elif not recommender.is_warmed_up:
                status_msg = "WARMING RISK ENGINE"
            else:
                status_msg = "FULLY OPERATIONAL"

            state = {
                "tick": simulator.time_tick,
                "ml_trained": True,
                "engine_status": status_msg,
                "hub_registry": "Synchronized"
            }

            await websocket.send_text(
                json.dumps(state)
            )

            await asyncio.sleep(2.0)

    except Exception as e:
        print(f"WebSocket closed: {e}")


@app.get("/api/cities")
def get_cities():
    """Returns the city-to-hub mapping for multimodal resolution."""
    path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "canonical_locations.json"
    )

    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)

    return {}


@app.post("/api/recommend")
def recommend_routes(req: RecommendRequest):

    # Validate currency before entering the routing engine.
    # This produces a clean API error instead of silently
    # displaying a wrong currency.
    currency = normalize_currency(req.currency)

    result = recommender.recommend(
        source=req.source,
        destination=req.destination,
        cargo_type=req.cargo_type,
        priority=req.priority,
        transport_preference=req.transport_preference,
        routing_policy=req.routing_policy,
        scenario=req.scenario,
        overrides=req.overrides,
        currency=currency
    )

    return result


@app.post("/api/suppliers")
def get_suppliers(req: SourcingRequest):

    # Get active disruptions from scenario manager
    active_disruptions = {}

    if req.scenario:
        scenario_mgr.activate_scenario(req.scenario)
        active_disruptions = (
            scenario_mgr.get_active_disruptions()
        )

    ranked_suppliers = supplier_scorer.get_ranked_suppliers(
        req.category,
        active_disruptions
    )

    advice = supplier_scorer.get_procurement_advice(
        req.current_inventory,
        req.safety_stock,
        req.demand_forecast
    )

    return {
        "suppliers": ranked_suppliers,
        "advice": advice,
        "active_disruptions": active_disruptions
    }

