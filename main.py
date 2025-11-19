import os
from datetime import datetime, date
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
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
    d = dict(doc)
    d["id"] = str(d.pop("_id"))
    return d

# ---------- Catalog Models ----------

class GameIdea(BaseModel):
    id: str
    title: str
    type: str
    difficulty: str
    tags: List[str] = []
    shortDescription: Optional[str] = None
    concept: Optional[str] = None
    coreMechanics: List[str] = []
    funHooks: List[str] = []
    monetizationIdeas: List[str] = []
    thumbnail3DUrl: Optional[str] = None
    heroImageUrl: Optional[str] = None
    recommendedLevel: Optional[str] = None

class EarnStep(BaseModel):
    stepNumber: int
    title: str
    explanation: str

class EarnChecklistItem(BaseModel):
    taskId: str
    label: str
    isOptional: bool = False

class EarnPath(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    steps: List[EarnStep] = []
    checklist: List[EarnChecklistItem] = []
    tips: List[str] = []
    heroImageUrl: Optional[str] = None

class WorldInspiration(BaseModel):
    id: str
    title: str
    tags: List[str] = []
    visualStyleNotes: Optional[str] = None
    useCases: List[str] = []
    buildChecklist: List[str] = []
    image3DUrl: Optional[str] = None

# ---------- Plan Models ----------

class TaskModel(BaseModel):
    taskId: Optional[str] = None
    label: str
    isDone: bool = False
    dueDate: Optional[str] = None
    completedAt: Optional[str] = None

class PlanCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(game|earning|challenge)$")
    linkedIdeaId: Optional[str] = None
    linkedPathId: Optional[str] = None
    robuxGoal: Optional[int] = None
    notes: Optional[str] = None
    tasks: List[TaskModel] = []

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(game|earning|challenge)$")
    linkedIdeaId: Optional[str] = None
    linkedPathId: Optional[str] = None
    robuxGoal: Optional[int] = None
    notes: Optional[str] = None
    tasks: Optional[List[TaskModel]] = None
    streakCount: Optional[int] = None

class TasksPatch(BaseModel):
    tasks: List[TaskModel]

class NotesPatch(BaseModel):
    notes: str

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

# ---------- Static Catalogs (Seeded) ----------

IDEAS: List[dict[str, Any]] = []
PATHS: List[dict[str, Any]] = []
WORLDS: List[dict[str, Any]] = []

# Seed function with rich content (trimmed for brevity but covers categories)

def seed_catalogs():
    global IDEAS, PATHS, WORLDS
    if IDEAS:
        return

    def idea(
        id: str, title: str, type_: str, difficulty: str, tags: list[str], concept: str,
        core: list[str], fun: list[str], monet: list[str], thumb: str, hero: str, level: str
    ):
        return {
            "id": id,
            "title": title,
            "type": type_,
            "difficulty": difficulty,
            "tags": tags,
            "shortDescription": concept[:120] + ("…" if len(concept) > 120 else ""),
            "concept": concept,
            "coreMechanics": core,
            "funHooks": fun,
            "monetizationIdeas": monet,
            "thumbnail3DUrl": thumb,
            "heroImageUrl": hero,
            "recommendedLevel": level,
        }

    # 20 ideas across categories
    IDEAS = [
        idea("idea-obby-lava", "Lava Parkour with Moving Platforms", "Obby", "Beginner", ["Obby","Parkour"],
             "Dash across floating islands above lava rivers. Time your jumps on moving platforms and collect coins to unlock shortcuts.",
             ["Jump timing", "Moving platforms", "Checkpoints", "Collectibles", "Speed pads"],
             ["Daily challenges", "Hidden rooms", "Co-op races", "Seasonal events"],
             ["Gamepasses: double coins, speed boost", "Dev products: shield, checkpoint skip", "Cosmetics: trails, pets"],
             "/images/idea_lava_obby.png", "/images/hero_lava_obby.png", "Beginner"),
        idea("idea-tycoon-pets", "Pet Rescue Tycoon", "Tycoon", "Intermediate", ["Tycoon","Pets","Simulator"],
             "Build a pet rescue center, treat animals, and expand rooms to serve more visitors.",
             ["Gather resources", "Upgrade rooms", "Mini-games for pet care", "NPC adoption system"],
             ["Events", "Rare pet drops", "Friend boosts"],
             ["Gamepasses: double income", "Dev products: boost packs", "Cosmetics: skins"],
             "/images/idea_pet_tycoon.png", "/images/hero_pet_tycoon.png", "Intermediate"),
        idea("idea-sim-mining", "Crystal Mining Simulator", "Simulator", "Beginner", ["Simulator","Mining"],
             "Mine colorful crystals, refine them, and sell to upgrade your drill.",
             ["Resource nodes", "Backpack capacity", "Refinery", "Upgrades"],
             ["Meteor showers", "Boss rock", "Obby shortcut caves"],
             ["Gamepasses: extra capacity", "Dev products: boost potions", "Cosmetics: pickaxe skins"],
             "/images/idea_mining.png", "/images/hero_mining.png", "Beginner"),
        idea("idea-role-cafe", "Cozy Cafe Roleplay", "Roleplay", "Beginner", ["Roleplay","Social"],
             "Run a cute cafe with friends, serve pastries, and decorate the shop.",
             ["Cooking mini-game", "Customer queue", "Decor placement", "Emotes"],
             ["Seasonal menus", "Competitions", "Photo mode"],
             ["Cosmetics", "Gamepasses: VIP lounge", "Premium payouts"],
             "/images/idea_cafe.png", "/images/hero_cafe.png", "Beginner"),
        idea("idea-horror-mansion", "Haunted Mansion Story", "Horror", "Intermediate", ["Horror","Story"],
             "Explore a spooky mansion, solve puzzles, and escape before midnight.",
             ["Inventory puzzles", "Chase sequences", "Light management"],
             ["Hidden endings", "Secret rooms"],
             ["Cosmetics only", "Premium payouts"],
             "/images/idea_horror_mansion.png", "/images/hero_horror_mansion.png", "Intermediate"),
        idea("idea-story-space", "Lost Astronaut Story", "Story", "Intermediate", ["Story","Sci-fi"],
             "Find a way home after your ship crashes on a neon planet.",
             ["Dialogue choices", "Crafting", "Exploration"],
             ["Time trials", "Photo collectibles"],
             ["Cosmetics: suits", "Dev products: temporary boosts"],
             "/images/idea_space.png", "/images/hero_space.png", "Intermediate"),
        idea("idea-pvp-arena", "Neon PvP Arena", "PvP", "Advanced", ["PvP","Action"],
             "Fast rounds in a compact neon arena with jump pads and powerups.",
             ["Round-based", "Powerups", "Team vs team"],
             ["Ranked ladder", "Season pass", "Clans"],
             ["Cosmetics", "Gamepasses: private servers", "Dev products: boosters"],
             "/images/idea_pvp.png", "/images/hero_pvp.png", "Advanced"),
        idea("idea-obby-ice", "Ice Cave Obby", "Obby", "Beginner", ["Obby","Winter"],
             "Slippery tunnels with sliding surfaces and falling icicles.",
             ["Slide physics", "Timed doors", "Checkpoints"],
             ["Speedrun boards", "Hidden penguin pet"],
             ["Cosmetics: trails", "Gamepasses: double coins"],
             "/images/idea_ice.png", "/images/hero_ice.png", "Beginner"),
        idea("idea-tycoon-mall", "Mini Mall Tycoon", "Tycoon", "Intermediate", ["Tycoon","Builder"],
             "Build a tiny mall with themed shops and hire NPCs.",
             ["Income tick", "Hire & upgrade NPCs", "Decor placement"],
             ["Events", "Limited-time shops"],
             ["Dev products: cash packs", "Gamepasses: double income", "Cosmetics: outfits"],
             "/images/idea_mall.png", "/images/hero_mall.png", "Intermediate"),
        idea("idea-sim-racing", "Cloud Kart Racer", "Simulator", "Beginner", ["Racing","Simulator"],
             "Arcade racing on cloud tracks with boosters and banners.",
             ["Time trials", "Kart upgrades", "Boost pads"],
             ["Ghost races", "Seasonal tracks"],
             ["Cosmetics: karts", "Season pass", "Dev products: boosters"],
             "/images/idea_race.png", "/images/hero_race.png", "Beginner"),
        idea("idea-role-hospital", "Mini Hospital Roleplay", "Roleplay", "Beginner", ["Roleplay","Builder"],
             "Treat patients in a friendly hospital and unlock new rooms.",
             ["Mini-games", "NPC schedules", "Decor"],
             ["Events", "Photo quests"],
             ["Cosmetics", "Premium payouts"],
             "/images/idea_hospital.png", "/images/hero_hospital.png", "Beginner"),
        idea("idea-horror-forest", "Whispering Forest", "Horror", "Intermediate", ["Horror"],
             "Survive nights in a foggy forest with a roaming creature.",
             ["Stealth", "Sound cues", "Crafting traps"],
             ["Leaderboards", "Hidden lore"],
             ["Cosmetics only"],
             "/images/idea_forest.png", "/images/hero_forest.png", "Intermediate"),
        idea("idea-story-school", "Mystery at Pixel High", "Story", "Beginner", ["Story","School"],
             "Solve a school mystery using clues and mini-puzzles.",
             ["Dialogue", "Puzzle rooms", "Collectibles"],
             ["Photo mode", "Multiple endings"],
             ["Cosmetics"],
             "/images/idea_school.png", "/images/hero_school.png", "Beginner"),
        idea("idea-pvp-battle-royale", "Tiny Battle Royale", "PvP", "Advanced", ["PvP","Shooter"],
             "Quick 12-player rounds on micro islands.",
             ["Drops", "Storm circle", "Attachments"],
             ["Ranked", "Clans"],
             ["Cosmetics", "Battle pass"],
             "/images/idea_battleroyale.png", "/images/hero_battleroyale.png", "Advanced"),
        idea("idea-obby-toy", "Toy Factory Obby", "Obby", "Beginner", ["Obby","Cute"],
             "Colorful conveyor belts and bouncy toys as obstacles.",
             ["Conveyors", "Jump pads", "Timing"],
             ["Daily quests", "Secret plushies"],
             ["Cosmetics", "Dev products: boosters"],
             "/images/idea_toy.png", "/images/hero_toy.png", "Beginner"),
        idea("idea-tycoon-farm", "Pixel Farm Tycoon", "Tycoon", "Beginner", ["Tycoon","Farm"],
             "Grow crops, upgrade tractors, sell at market.",
             ["Plant/harvest", "Upgrades", "Delivery quests"],
             ["Seasonal crops", "Friend boosts"],
             ["Gamepasses: double yield", "Cosmetics: skins"],
             "/images/idea_farm.png", "/images/hero_farm.png", "Beginner"),
        idea("idea-sim-bakery", "Bakery Simulator", "Simulator", "Beginner", ["Simulator","Cooking"],
             "Mix ingredients, bake pastries, and decorate your shop.",
             ["Recipe mini-games", "Upgrades", "Delivery"],
             ["Events", "Photo mode"],
             ["Cosmetics", "Boost packs"],
             "/images/idea_bakery.png", "/images/hero_bakery.png", "Beginner"),
        idea("idea-role-city", "Mini City Roleplay", "Roleplay", "Intermediate", ["Roleplay","City"],
             "Jobs, apartments, vehicles in a tiny city.",
             ["Job mini-games", "Housing", "Vehicles"],
             ["Events", "Photo mode"],
             ["Cosmetics", "Premium payouts"],
             "/images/idea_city.png", "/images/hero_city.png", "Intermediate"),
        idea("idea-horror-lab", "Lab Escape", "Horror", "Advanced", ["Horror","Sci-fi"],
             "Escape a glitchy lab with puzzles and stealth.",
             ["Stealth", "Puzzles", "Chase"],
             ["Speedrun", "Hidden endings"],
             ["Cosmetics only"],
             "/images/idea_lab.png", "/images/hero_lab.png", "Advanced"),
        idea("idea-story-fantasy", "Crystal Kingdom", "Story", "Beginner", ["Story","Fantasy"],
             "Restore a shattered kingdom by finding crystal shards.",
             ["Exploration", "Boss fights", "Crafting"],
             ["Photo mode", "Quests"],
             ["Cosmetics"],
             "/images/idea_crystal.png", "/images/hero_crystal.png", "Beginner"),
    ]

    def path(id: str, title: str, slug: str, description: str, steps: list[tuple[str, str]], checklist: list[tuple[str, bool]], tips: list[str], hero: str):
        return {
            "id": id,
            "title": title,
            "slug": slug,
            "description": description,
            "steps": [
                {"stepNumber": i + 1, "title": s[0], "explanation": s[1]} for i, s in enumerate(steps)
            ],
            "checklist": [
                {"taskId": f"{id}-t{i}", "label": lbl, "isOptional": opt} for i, (lbl, opt) in enumerate(checklist)
            ],
            "tips": tips,
            "heroImageUrl": hero,
        }

    PATHS = [
        path(
            "path-create-games",
            "Create Games",
            "create-games",
            "Earn Robux by building and publishing fair, fun experiences.",
            [
                ("Learn Roblox Studio basics", "Follow official tutorials and build small scenes."),
                ("Publish a simple experience", "Ship a tiny obby or cafe to learn the flow."),
                ("Add gamepasses/dev products", "Offer fair boosts and cosmetic items only."),
                ("Add analytics & iterate", "Watch retention and improve weekly."),
                ("Promote safely", "Use social posts and collaborate, no spam.")
            ],
            [
                ("Install Roblox Studio", False),
                ("Ship your first tiny game", False),
                ("Add 1 cosmetic and 1 boost", False),
                ("Test with 3 friends", False),
                ("Read TOS monetization rules", True)
            ],
            ["Test with friends", "Focus on fun first", "Respect TOS", "Iterate weekly"],
            "/images/path_create_games.png",
        ),
        path(
            "path-ugc-items",
            "Create UGC Items",
            "ugc-items",
            "Design hats and accessories that follow UGC rules.",
            [
                ("Learn a 3D tool (Blender)", "Model simple shapes and export correctly."),
                ("Understand submission rules", "Check sizes, textures, and categories."),
                ("Create 3 test items", "Iterate on style and theme."),
                ("Thumbnails & promotion", "Clear renders with good lighting."),
                ("Collaborate with creators", "Bundles and cross-promotions.")
            ],
            [
                ("Pick a modeling workflow", False),
                ("Create 1 hat prototype", False),
                ("Render & preview in Studio", False),
                ("Read UGC guidelines", True)
            ],
            ["Trendy yet readable", "Clean thumbnails", "Optimize polycounts"],
            "/images/path_ugc.png",
        ),
        path(
            "path-gamepasses",
            "Gamepasses & Dev Products",
            "gamepasses",
            "Fair ways to monetize experiences without pay-to-win.",
            [
                ("Design meaningful cosmetics", "Trails, emotes, pets"),
                ("Offer convenience boosts", "Respect balance; avoid p2w"),
                ("Price testing", "Start low and adjust"),
                ("A/B test variants", "See what players value"),
                ("Support & refunds", "Keep trust high"),
            ],
            [
                ("List 5 cosmetic ideas", False),
                ("Design 3 useful boosts", False),
                ("Set initial prices", False),
                ("Test with friends", False)
            ],
            ["Always fair", "Clear value", "No gambling"],
            "/images/path_gamepasses.png",
        ),
        path(
            "path-commissions",
            "Commissions & Building for Others",
            "commissions",
            "Earn by helping teams with building, UI, or scripting.",
            [
                ("Create a mini portfolio", "3 screenshots + role description"),
                ("Join safe communities", "Discords, forums with rules"),
                ("Deliver small gigs", "Fast feedback loops"),
                ("Request testimonials", "Build credibility"),
                ("Scale pricing", "Packages for work")
            ],
            [
                ("Make a portfolio page", False),
                ("Finish 1 paid mini gig", False),
                ("Ask for testimonial", False)
            ],
            ["Avoid scams", "Contracts up front", "Be reliable"],
            "/images/path_commissions.png",
        ),
        path(
            "path-premium-payouts",
            "Roblox Premium/Engagement Payouts",
            "premium-payouts",
            "Design for healthy engagement to qualify for payouts.",
            [
                ("Review Premium rules", "Check current policies in docs"),
                ("Improve day-1 fun", "Great first 5 minutes"),
                ("Improve day-7 retention", "Reasons to return"),
                ("Ethical loops", "No dark patterns"),
                ("Ship content updates", "Predictable cadence")
            ],
            [
                ("Read official rules", False),
                ("Add daily/weekly quests", False),
                ("Run retention test", False)
            ],
            ["Fun first", "Healthy loops", "Respect players"],
            "/images/path_premium.png",
        ),
    ]

    def world(id: str, title: str, tags: list[str], notes: str, uses: list[str], checklist: list[str], img: str):
        return {
            "id": id,
            "title": title,
            "tags": tags,
            "visualStyleNotes": notes,
            "useCases": uses,
            "buildChecklist": checklist,
            "image3DUrl": img,
        }

    WORLDS = [
        world("world-floating-islands", "Floating Islands", ["lobby","fantasy"], "Soft clouds, pastel rocks, coins floating.", ["Lobby","Spawn","Parkour"], ["Chunky islands","Jump pads","Coins"], "/images/world_islands.png"),
        world("world-cute-shop", "Cute Pet Shop", ["shop","cute"], "Warm lights, rounded shelves, plush props.", ["Shop","UI bg"], ["Counter","Shelves","Cash register"], "/images/world_shop.png"),
        world("world-sci-hub", "Sci‑Fi Hub", ["sci-fi","hub"], "Neon trims, hex panels, fog.", ["Hub","Teleporter"], ["Portal rings","Holograms","Pipes"], "/images/world_sci.png"),
        world("world-cloud-track", "Cloud Track", ["race","sport"], "High contrast track, boosters, banners.", ["Race","Time trial"], ["Track loops","Boosters","Banners"], "/images/world_track.png"),
        world("world-lava-cave", "Lava Cave", ["obby","lava"], "Orange glow, smoke, crystals.", ["Obby","Mine"], ["Lava rivers","Crystals","Falling rocks"], "/images/world_lava.png"),
        world("world-winter-town", "Winter Town", ["cozy","winter"], "Snow sparkle, wood cabins, lights.", ["Roleplay","Events"], ["Cabins","Trees","Market"], "/images/world_winter.png"),
        world("world-space-port", "Space Port", ["sci-fi"], "Steel floors, blinking lights, panels.", ["Hub","Story"], ["Dock","Control room","Hallway"], "/images/world_space.png"),
        world("world-beach-resort", "Beach Resort", ["summer","roleplay"], "Turquoise water, palm trees, towels.", ["Roleplay","Racing"], ["Bungalows","Pier","Karts"], "/images/world_beach.png"),
        world("world-forest-camp", "Forest Camp", ["nature","cozy"], "Green fog, campfire, tents.", ["Roleplay","Story"], ["Campfire","Tents","Lake"], "/images/world_forest.png"),
        world("world-city-neon", "Neon City", ["city","neon"], "Wet asphalt, neon signs, reflections.", ["PvP","Racing"], ["Alleys","Billboards","Crosswalks"], "/images/world_city.png"),
        world("world-sky-castle", "Sky Castle", ["fantasy"], "Crystal towers, floating shards, banners.", ["Story","Boss"], ["Bridge","Throne","Crystal garden"], "/images/world_castle.png"),
        world("world-desert-ruins", "Desert Ruins", ["desert","explore"], "Dust, sandstone, statues.", ["Story","Obby"], ["Pillars","Traps","Relics"], "/images/world_desert.png"),
    ]

seed_catalogs()

# ---------- Catalog Endpoints ----------

@app.get("/api/ideas")
def list_ideas(type: Optional[str] = Query(None), difficulty: Optional[str] = Query(None), tag: Optional[str] = Query(None), q: Optional[str] = Query(None)):
    data = IDEAS
    if type:
        data = [i for i in data if i["type"].lower() == type.lower()]
    if difficulty:
        data = [i for i in data if i["difficulty"].lower() == difficulty.lower()]
    if tag:
        data = [i for i in data if tag in i.get("tags", [])]
    if q:
        ql = q.lower()
        data = [i for i in data if ql in (i["title"].lower() + " " + (i.get("concept") or "").lower())]
    return data

@app.get("/api/ideas/{idea_id}")
def get_idea(idea_id: str):
    idea = next((i for i in IDEAS if i["id"] == idea_id), None)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea

# Keep legacy endpoint for compatibility
@app.get("/api/earning-paths")
def list_paths_legacy():
    return PATHS

@app.get("/api/earning-paths/{path_id}")
def get_path_legacy(path_id: str):
    p = next((x for x in PATHS if x["id"] == path_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Path not found")
    return p

@app.get("/api/paths")
def list_paths():
    return PATHS

@app.get("/api/paths/{path_id}")
def get_path(path_id: str):
    p = next((x for x in PATHS if x["id"] == path_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Path not found")
    return p

@app.get("/api/worlds")
def list_worlds(tag: Optional[str] = Query(None), q: Optional[str] = Query(None)):
    data = WORLDS
    if tag:
        data = [w for w in data if tag in w.get("tags", [])]
    if q:
        ql = q.lower()
        data = [w for w in data if ql in (w["title"].lower() + " " + (w.get("visualStyleNotes") or "").lower())]
    return data

@app.get("/api/worlds/{world_id}")
def get_world(world_id: str):
    w = next((x for x in WORLDS if x["id"] == world_id), None)
    if not w:
        raise HTTPException(status_code=404, detail="World not found")
    return w

# ---------- Plans (MongoDB) ----------

def calc_progress(tasks: list[dict]) -> int:
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.get("isDone"))
    return int(done / len(tasks) * 100)

@app.get("/api/plans")
def get_plans():
    docs = get_documents("plan") if db is not None else []
    return [doc_to_dict(d) for d in docs]

@app.post("/api/plans")
def create_plan(payload: PlanCreate):
    tasks = [t.model_dump() for t in payload.tasks]

    # enrich from linked idea/path
    if payload.linkedIdeaId:
        idea = next((i for i in IDEAS if i["id"] == payload.linkedIdeaId), None)
        if idea:
            if not payload.notes:
                payload.notes = idea.get("concept")
            # default tasks from mechanics and monetization
            for label in (idea.get("coreMechanics", [])[:3] + idea.get("funHooks", [])[:2]):
                tasks.append({"label": f"Design: {label}", "isDone": False})
            for label in idea.get("monetizationIdeas", [])[:2]:
                tasks.append({"label": f"Plan monetization: {label}", "isDone": False})
    if payload.linkedPathId:
        path = next((p for p in PATHS if p["id"] == payload.linkedPathId), None)
        if path:
            if not payload.notes:
                payload.notes = path.get("description")
            for c in path.get("checklist", [])[:6]:
                tasks.append({"label": c.get("label", "Task"), "isDone": False})

    now = datetime.utcnow().isoformat()
    for idx, t in enumerate(tasks):
        if not t.get("taskId"):
            t["taskId"] = f"t{idx}-{int(datetime.utcnow().timestamp())}"
        t.setdefault("isDone", False)

    data = {
        "name": payload.name,
        "type": payload.type,
        "linkedIdeaId": payload.linkedIdeaId,
        "linkedPathId": payload.linkedPathId,
        "robuxGoal": payload.robuxGoal,
        "notes": payload.notes or "",
        "tasks": tasks,
        "progressPercent": calc_progress(tasks),
        "streakCount": 0,
        "lastCompletedDate": None,
        "createdAt": now,
        "updatedAt": now,
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

@app.put("/api/plans/{plan_id}")
def put_plan(plan_id: str, payload: PlanUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    update = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k != "tasks"}
    now = datetime.utcnow().isoformat()
    update["updatedAt"] = now
    res = db["plan"].update_one({"_id": to_object_id(plan_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    doc = db["plan"].find_one({"_id": to_object_id(plan_id)})
    return doc_to_dict(doc)

@app.patch("/api/plans/{plan_id}/tasks")
def patch_tasks(plan_id: str, payload: TasksPatch):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    plan = db["plan"].find_one({"_id": to_object_id(plan_id)})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    incoming = [t.model_dump() for t in payload.tasks]

    # streak logic: if any task transitions to done today
    today = date.today().isoformat()
    prev_last = plan.get("lastCompletedDate")
    completed_today = False

    # Normalize tasks and detect completions
    for t in incoming:
        if not t.get("taskId"):
            t["taskId"] = f"t-{int(datetime.utcnow().timestamp())}"
        if t.get("isDone") and not t.get("completedAt"):
            t["completedAt"] = datetime.utcnow().isoformat()
            completed_today = True

    # Update streak
    streak = plan.get("streakCount", 0) or 0
    last_day = prev_last
    if completed_today:
        if last_day == today:
            pass  # already counted today
        elif last_day is None:
            streak = 1
        else:
            # check consecutive
            try:
                last_d = date.fromisoformat(last_day)
                if (date.today() - last_d).days == 1:
                    streak += 1
                else:
                    streak = 1
            except Exception:
                streak = 1
        last_day = today

    progress = calc_progress(incoming)
    now = datetime.utcnow().isoformat()
    res = db["plan"].update_one(
        {"_id": to_object_id(plan_id)},
        {"$set": {
            "tasks": incoming,
            "progressPercent": progress,
            "streakCount": streak,
            "lastCompletedDate": last_day,
            "updatedAt": now,
        }}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    doc = db["plan"].find_one({"_id": to_object_id(plan_id)})
    return doc_to_dict(doc)

@app.patch("/api/plans/{plan_id}/notes")
def patch_notes(plan_id: str, payload: NotesPatch):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    now = datetime.utcnow().isoformat()
    res = db["plan"].update_one({"_id": to_object_id(plan_id)}, {"$set": {"notes": payload.notes, "updatedAt": now}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    doc = db["plan"].find_one({"_id": to_object_id(plan_id)})
    return doc_to_dict(doc)

@app.delete("/api/plans/{plan_id}")
def delete_plan(plan_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["plan"].delete_one({"_id": to_object_id(plan_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
