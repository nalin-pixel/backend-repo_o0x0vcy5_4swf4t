import os
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Roblox Idea Lab & Robux Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers ----------

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

def doc_to_dict(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

# ---------- Models for requests ----------

class TaskModel(BaseModel):
    title: str
    done: bool = False
    due_date: Optional[str] = None
    icon: Optional[str] = None

class PlanCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(game|earning|challenge)$")
    description: Optional[str] = None
    goal_robux: Optional[int] = None
    idea_id: Optional[str] = None
    earning_path_id: Optional[str] = None
    tasks: List[TaskModel] = []

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    goal_robux: Optional[int] = None
    tasks: Optional[List[TaskModel]] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    streak_days: Optional[int] = None

# ---------- Health ----------

@app.get("/")
def root():
    return {"message": "Roblox Idea Lab API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                cols = db.list_collection_names()
                response["collections"] = cols[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------- Static Catalogs (Ideas & Earning Paths) ----------

IDEAS: List[dict[str, Any]] = [
    {
        "id": "idea-obby-lava",
        "title": "Lava Parkour with Moving Platforms",
        "tags": ["Obby", "Parkour", "Beginner"],
        "difficulty": "Easy",
        "type": "Obby",
        "multiplayer": True,
        "image": "/images/idea_lava_obby.png",
        "concept": "Classic obby across floating islands with lava rivers and timed platforms.",
        "mechanics": ["Jumping", "Timing", "Checkpoints", "Collect coins"],
        "fun": ["Daily quests", "Hidden secrets", "Weekly leaderboard"],
        "monetization": [
            "Gamepasses: extra speed, double coins",
            "Dev products: temporary shield, checkpoint skip",
            "Cosmetics: trails, pets"
        ],
    },
    {
        "id": "idea-tycoon-pets",
        "title": "Pet Rescue Tycoon",
        "tags": ["Tycoon", "Pets", "Simulator"],
        "difficulty": "Medium",
        "type": "Tycoon",
        "multiplayer": True,
        "image": "/images/idea_pet_tycoon.png",
        "concept": "Build and upgrade a pet rescue center, adopt out pets, and expand rooms.",
        "mechanics": ["Gather resources", "Upgrades", "Idle income", "Pet care mini-games"],
        "fun": ["Events", "Rare pet drops", "Co-op boosts"],
        "monetization": ["Gamepasses: double income", "Dev products: boost packs", "Cosmetics: skins"]
    },
    {
        "id": "idea-horror-mansion",
        "title": "Haunted Mansion Story",
        "tags": ["Horror", "Story"],
        "difficulty": "Medium",
        "type": "Story",
        "multiplayer": False,
        "image": "/images/idea_horror_mansion.png",
        "concept": "Narrative exploration with puzzles and light jumpscares in a spooky mansion.",
        "mechanics": ["Exploration", "Puzzles", "Inventory"],
        "fun": ["Hidden rooms", "Multiple endings"],
        "monetization": ["Cosmetics only: flashlight skins, outfits"]
    }
]

EARNING_PATHS: List[dict[str, Any]] = [
    {
        "id": "path-create-games",
        "title": "Create Games",
        "overview": "Earn Robux by building and publishing your own experiences.",
        "steps": [
            "Learn basics of Roblox Studio",
            "Publish your first simple game",
            "Add gamepasses and dev products",
            "Add daily rewards and analytics",
            "Optimize monetization fairly"
        ],
        "checklist": [
            {"title": "Install Roblox Studio", "done": False, "icon": "download"},
            {"title": "Follow a beginner tutorial", "done": False, "icon": "book"},
            {"title": "Publish a test place", "done": False, "icon": "upload"}
        ],
        "tips": ["Test with friends", "Watch analytics", "Iterate weekly"],
        "image": "/images/path_create_games.png"
    },
    {
        "id": "path-ugc-items",
        "title": "Create UGC Items",
        "overview": "Design hats and accessories for the marketplace.",
        "steps": ["Learn modeling basics", "Follow submission rules", "Promote your items"],
        "checklist": [
            {"title": "Pick a 3D tool (Blender)", "done": False},
            {"title": "Create 1 test hat", "done": False},
            {"title": "Render and preview", "done": False}
        ],
        "tips": ["Trendy but unique", "Clear thumbnails"],
        "image": "/images/path_ugc.png"
    }
]

@app.get("/api/ideas")
def list_ideas():
    return IDEAS

@app.get("/api/ideas/{idea_id}")
def get_idea(idea_id: str):
    for idea in IDEAS:
        if idea["id"] == idea_id:
            return idea
    raise HTTPException(status_code=404, detail="Idea not found")

@app.get("/api/earning-paths")
def list_paths():
    return EARNING_PATHS

@app.get("/api/earning-paths/{path_id}")
def get_path(path_id: str):
    for p in EARNING_PATHS:
        if p["id"] == path_id:
            return p
    raise HTTPException(status_code=404, detail="Path not found")

# ---------- Plans (MongoDB) ----------

@app.get("/api/plans")
def get_plans():
    docs = get_documents("plan") if db is not None else []
    return [doc_to_dict(d) for d in docs]

@app.post("/api/plans")
def create_plan(payload: PlanCreate):
    # If creating from idea/path, enrich description/tasks
    tasks = [t.model_dump() for t in payload.tasks]

    if payload.idea_id:
        idea = next((i for i in IDEAS if i["id"] == payload.idea_id), None)
        if idea:
            if not payload.description:
                payload.description = idea["concept"]
            # seed tasks from mechanics
            for m in idea.get("mechanics", [])[:5]:
                tasks.append({"title": f"Build: {m}", "done": False})
    if payload.earning_path_id:
        path = next((p for p in EARNING_PATHS if p["id"] == payload.earning_path_id), None)
        if path:
            if not payload.description:
                payload.description = path["overview"]
            for c in path.get("checklist", [])[:5]:
                tasks.append({"title": c.get("title", "Task"), "done": False})

    data = {
        "name": payload.name,
        "type": payload.type,
        "description": payload.description,
        "goal_robux": payload.goal_robux,
        "idea_id": payload.idea_id,
        "earning_path_id": payload.earning_path_id,
        "tasks": tasks,
        "progress": 0,
        "streak_days": 0,
    }
    new_id = create_document("plan", data)
    doc = db["plan"].find_one({"_id": ObjectId(new_id)}) if db is not None else None
    return doc_to_dict(doc) if doc else {"id": new_id, **data}

@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["plan"].find_one({"_id": to_object_id(plan_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Plan not found")
    return doc_to_dict(doc)

@app.patch("/api/plans/{plan_id}")
def update_plan(plan_id: str, payload: PlanUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    update: dict[str, Any] = {k: v for k, v in payload.model_dump(exclude_none=True).items()}

    # Auto-calc progress if tasks provided
    if "tasks" in update and update["tasks"] is not None:
        tasks = update["tasks"]
        if isinstance(tasks, list) and tasks:
            done = sum(1 for t in tasks if t.get("done"))
            update["progress"] = int((done / len(tasks)) * 100)
    res = db["plan"].update_one({"_id": to_object_id(plan_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    doc = db["plan"].find_one({"_id": to_object_id(plan_id)})
    return doc_to_dict(doc)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
