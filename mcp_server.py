from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import os
import json

mcp = FastMCP("ArchSpec-Pricing-Server")

VENDORS_DB_PATH = os.path.join(os.path.dirname(__file__), "vendors_db.json")

def load_db():
    if not os.path.exists(VENDORS_DB_PATH):
        return {}
    with open(VENDORS_DB_PATH, "r") as f:
        return json.load(f)

@mcp.tool()
def fetch_market_pricing(category: str) -> str:
    """Fetch pricing options (Standard, Mid-Range, Premium) for a specific material category."""
    db = load_db()
    matrix = db.get("material_matrix", {})
    if category in matrix:
        return json.dumps(matrix[category])
    return json.dumps({"error": f"Category {category} not found."})

@mcp.tool()
def match_and_route_builder(total_budget: float) -> str:
    """Find and route to verified builders in Ontario/GTA based on total project budget."""
    db = load_db()
    builders = db.get("builders", [])
    
    if total_budget < 150000:
        bracket = "Standard"
    elif total_budget < 600000:
        bracket = "Mid-Range"
    else:
        bracket = "Luxury Custom Home Builders"
        
    matched = [b for b in builders if b.get("bracket") == bracket]
    return json.dumps({
        "bracket": bracket,
        "builders": matched
    })

app = FastAPI(title="ArchSpec AI MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST Endpoint 1
@app.get("/fetch_market_pricing")
async def get_pricing(category: str):
    db = load_db()
    matrix = db.get("material_matrix", {})
    if category in matrix:
        return matrix[category]
    raise HTTPException(status_code=404, detail=f"Category {category} not found")

# REST Endpoint 2
@app.get("/match_and_route_builder")
async def route_builders(total_budget: float):
    db = load_db()
    builders = db.get("builders", [])
    
    if total_budget < 150000:
        bracket = "Standard"
    elif total_budget < 600000:
        bracket = "Mid-Range"
    else:
        bracket = "Luxury Custom Home Builders"
        
    matched = [b for b in builders if b.get("bracket") == bracket]
    return {
        "bracket": bracket,
        "builders": matched
    }

# Mount MCP SSE app at root
app.mount("/", mcp.sse_app())
