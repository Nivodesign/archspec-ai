import json
import os
import httpx

class AgentState:
    def __init__(self, project_id: str, scope: str, area: float, image_path: str):
        self.project_id = project_id
        self.scope = scope  # "Exterior" or "Interior"
        self.area = area
        self.image_path = image_path
        self.status = "START"
        self.detected_materials = []  # List of {"category": str, "detected_spec": str}
        self.pricing_matrix = {}      # Dict of category -> {"Standard": float, "Mid-Range": float, "Premium": float}
        self.selected_tiers = {}      # Dict of category -> "Standard" / "Mid-Range" / "Premium"
        self.total_budget = 0.0
        self.routed_builders = []

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "scope": self.scope,
            "area": self.area,
            "image_path": self.image_path,
            "status": self.status,
            "detected_materials": self.detected_materials,
            "pricing_matrix": self.pricing_matrix,
            "selected_tiers": self.selected_tiers,
            "total_budget": self.total_budget,
            "routed_builders": self.routed_builders
        }

    @classmethod
    def from_dict(cls, data: dict):
        state = cls(data["project_id"], data["scope"], float(data["area"]), data["image_path"])
        state.status = data.get("status", "START")
        state.detected_materials = data.get("detected_materials", [])
        state.pricing_matrix = data.get("pricing_matrix", {})
        state.selected_tiers = data.get("selected_tiers", {})
        state.total_budget = float(data.get("total_budget", 0.0))
        state.routed_builders = data.get("routed_builders", [])
        return state

class ArchitecturalSpecParserGraph:
    def __init__(self, mcp_server_url: str = "http://127.0.0.1:8001"):
        self.mcp_server_url = mcp_server_url
        self.db_path = os.path.join(os.path.dirname(__file__), "vendors_db.json")

    def run_next(self, state: AgentState) -> AgentState:
        """Execute the next node in the state graph based on current status."""
        if state.status == "START":
            return self.run_vision_node(state)
        elif state.status == "VISION_NODE":
            return self.run_procurement_node(state)
        elif state.status == "PROCUREMENT_NODE":
            return self.run_gate_node(state)
        elif state.status == "ROUTING_NODE":
            return self.run_routing_node(state)
        return state

    def run_vision_node(self, state: AgentState) -> AgentState:
        state.status = "VISION_NODE"
        # Parse image layers strictly based on the scope
        filename = os.path.basename(state.image_path).lower() if state.image_path else ""
        
        if state.scope == "Exterior":
            # 6 Exterior Schemas
            state.detected_materials = [
                {
                    "category": "cladding",
                    "detected_spec": "Modern fiber cement panels with natural wood cladding highlights" if "wood" in filename else "Classic red architectural clay brick cladding"
                },
                {
                    "category": "roofing",
                    "detected_spec": "Standing seam metal roofing panels (charcoal grey)" if "metal" in filename else "Architectural asphalt shingles (dual-black)"
                },
                {
                    "category": "glazing",
                    "detected_spec": "Triple-glazed low-E argon-filled aluminum frames"
                },
                {
                    "category": "openings_ext",
                    "detected_spec": "Insulated fiberglass entry doors & smart garage door units"
                },
                {
                    "category": "insulation_ext",
                    "detected_spec": "Continuous rigid rockwool board insulation (R-10)"
                },
                {
                    "category": "decking_patio",
                    "detected_spec": "Composite low-maintenance decking boards on pressure-treated framing"
                }
            ]
        else:
            # 10 Interior Schemas
            state.detected_materials = [
                {
                    "category": "flooring",
                    "detected_spec": "Engineered white oak hardwood flooring" if "wood" in filename else "Polished porcelain tile flooring (60x60)"
                },
                {
                    "category": "wall_finish",
                    "detected_spec": "Level 5 smooth-finish gypsum board drywall"
                },
                {
                    "category": "ceilings",
                    "detected_spec": "Acoustic drywall ceilings with integrated recessed channels"
                },
                {
                    "category": "openings_int",
                    "detected_spec": "Solid core slab interior doors with satin nickel hardware"
                },
                {
                    "category": "millwork",
                    "detected_spec": "Modern flat-profile baseboards & casings (MDF)"
                },
                {
                    "category": "cabinetry",
                    "detected_spec": "Custom flat-panel kitchen cabinetry with soft-close hinges"
                },
                {
                    "category": "countertops",
                    "detected_spec": "Quartz countertop slab with mitered waterfall edge"
                },
                {
                    "category": "plumbing",
                    "detected_spec": "Undermount sinks with matte black single-handle pull-down faucets"
                },
                {
                    "category": "lighting",
                    "detected_spec": "Recessed LED gimbal potlights & linear kitchen island pendants"
                },
                {
                    "category": "insulation_int",
                    "detected_spec": "Acoustic stone wool batt insulation in partition walls"
                }
            ]
        
        # Auto-advance to Procurement Node
        return self.run_procurement_node(state)

    def run_procurement_node(self, state: AgentState) -> AgentState:
        state.status = "PROCUREMENT_NODE"
        # Fetch pricing matrix for each detected material category
        for mat in state.detected_materials:
            category = mat["category"]
            pricing = self._fetch_pricing(category)
            if pricing:
                state.pricing_matrix[category] = pricing
        
        # Advance to Gate Node where it will pause
        return self.run_gate_node(state)

    def run_gate_node(self, state: AgentState) -> AgentState:
        # Pauses the loop in a safe PAUSED state until HITL interaction
        state.status = "PAUSED"
        return state

    def resume_with_selections(self, state: AgentState, selected_tiers: dict) -> AgentState:
        """Resume execution of the graph by supplying human-in-the-loop tier selections."""
        if state.status != "PAUSED":
            raise ValueError(f"Graph is not in PAUSED state. Current state: {state.status}")
            
        state.selected_tiers = selected_tiers
        
        # Calculate Total Estimated Project Cost
        total_unit_cost = 0.0
        for mat in state.detected_materials:
            category = mat["category"]
            tier = selected_tiers.get(category, "Standard")
            category_pricing = state.pricing_matrix.get(category, {})
            unit_cost = category_pricing.get(tier, 0.0)
            total_unit_cost += unit_cost
            
        state.total_budget = total_unit_cost * state.area
        state.status = "ROUTING_NODE"
        
        # Advance to Routing Node
        return self.run_routing_node(state)

    def run_routing_node(self, state: AgentState) -> AgentState:
        state.status = "ROUTING_NODE"
        # Find verified builders matching the budget
        routing_data = self._route_builders(state.total_budget)
        state.routed_builders = routing_data.get("builders", [])
        state.status = "COMPLETED"
        return state

    def _fetch_pricing(self, category: str) -> dict:
        # Try contacting MCP server, fallback to local file
        try:
            response = httpx.get(f"{self.mcp_server_url}/fetch_market_pricing", params={"category": category}, timeout=1.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass

        # Fallback to local vendors_db.json
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, "r") as f:
                    db = json.load(f)
                    return db.get("material_matrix", {}).get(category)
        except Exception:
            pass
        return None

    def _route_builders(self, total_budget: float) -> dict:
        # Try contacting MCP server, fallback to local file
        try:
            response = httpx.get(f"{self.mcp_server_url}/match_and_route_builder", params={"total_budget": total_budget}, timeout=1.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass

        # Fallback to local vendors_db.json
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, "r") as f:
                    db = json.load(f)
                    builders = db.get("builders", [])
                    if total_budget < 150000:
                        bracket = "Standard"
                    elif total_budget < 600000:
                        bracket = "Mid-Range"
                    else:
                        bracket = "Luxury Custom Home Builders"
                    matched = [b for b in builders if b.get("bracket") == bracket]
                    return {"bracket": bracket, "builders": matched}
        except Exception:
            pass
        return {"bracket": "Unknown", "builders": []}

def architectural_spec_parser(project_id: str, scope: str, area: float, image_path: str, mcp_url: str = "http://127.0.0.1:8001") -> dict:
    """Entry point for the architectural_spec_parser skill. Initializes and runs the graph."""
    state = AgentState(project_id, scope, area, image_path)
    graph = ArchitecturalSpecParserGraph(mcp_server_url=mcp_url)
    state = graph.run_next(state)
    return state.to_dict()
