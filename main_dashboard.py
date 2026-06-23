from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
from agent_graph import AgentState, ArchitecturalSpecParserGraph

app = FastAPI(title="ArchSpec AI Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECTS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(PROJECTS_CACHE_DIR, exist_ok=True)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_project_state(state: AgentState):
    cache_path = os.path.join(PROJECTS_CACHE_DIR, f"{state.project_id}.json")
    with open(cache_path, "w") as f:
        json.dump(state.to_dict(), f, indent=2)

def load_project_state(project_id: str) -> AgentState:
    cache_path = os.path.join(PROJECTS_CACHE_DIR, f"{project_id}.json")
    if not os.path.exists(cache_path):
        raise HTTPException(status_code=404, detail="Project not found")
    with open(cache_path, "r") as f:
        data = json.load(f)
    return AgentState.from_dict(data)

@app.post("/api/upload")
async def upload_project(
    scope: str = Form(...),
    area: float = Form(...),
    image: UploadFile = File(...)
):
    project_id = str(uuid.uuid4())
    
    # Save the file
    ext = os.path.splitext(image.filename)[1]
    filename = f"{project_id}{ext}"
    image_path = os.path.join(UPLOAD_DIR, filename)
    with open(image_path, "wb") as f:
        content = await image.read()
        f.write(content)
        
    # Initialize state
    state = AgentState(project_id, scope, area, image_path)
    
    # Run the graph (which executes Vision Node -> Procurement Node -> Pauses at Gate Node)
    graph = ArchitecturalSpecParserGraph(mcp_server_url="http://127.0.0.1:8001")
    state = graph.run_next(state)
    
    save_project_state(state)
    return state.to_dict()

@app.get("/api/project/{project_id}")
async def get_project(project_id: str):
    state = load_project_state(project_id)
    return state.to_dict()

@app.post("/api/project/{project_id}/select_tiers")
async def select_tiers(project_id: str, payload: dict):
    state = load_project_state(project_id)
    selected_tiers = payload.get("selected_tiers", {})
    
    graph = ArchitecturalSpecParserGraph(mcp_server_url="http://127.0.0.1:8001")
    try:
        state = graph.resume_with_selections(state, selected_tiers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    save_project_state(state)
    return state.to_dict()

# Serve index.html on root
@app.get("/")
async def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>static/index.html not found!</h1>", status_code=404)

# Mount uploads and static
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
