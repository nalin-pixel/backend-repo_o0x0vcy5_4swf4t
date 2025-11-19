"""
Database Schemas for Roblox Idea Lab & Robux Planner

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
These are used for validation and for the database viewer.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Core saved entities

class Task(BaseModel):
    title: str = Field(..., description="Task title")
    done: bool = Field(False, description="Completion state")
    due_date: Optional[str] = Field(None, description="ISO date string, optional")
    icon: Optional[str] = Field(None, description="Optional icon keyword")

class Plan(BaseModel):
    name: str = Field(..., description="Project/plan name")
    type: str = Field(..., description="game | earning | challenge")
    description: Optional[str] = Field(None, description="Short summary")
    goal_robux: Optional[int] = Field(None, description="Target Robux goal")
    idea_id: Optional[str] = Field(None, description="Linked idea ID if any")
    earning_path_id: Optional[str] = Field(None, description="Linked earning path ID if any")
    tasks: List[Task] = Field(default_factory=list, description="Task checklist")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage 0-100")
    streak_days: int = Field(0, description="Days in a row with at least one completed task")

class Inspiration(BaseModel):
    title: str = Field(..., description="Inspiration title")
    style_notes: Optional[str] = Field(None, description="Notes about colors, shapes, atmosphere")
    use_cases: List[str] = Field(default_factory=list, description="Where it can be used")
    build_checklist: List[str] = Field(default_factory=list, description="Parts to model")
    favorite: bool = Field(False, description="User favorited or not")

# Optional: store lightweight idea bookmarks (ideas catalog can be static)
class IdeaBookmark(BaseModel):
    idea_id: str = Field(..., description="Static catalog idea ID")
    title: str = Field(..., description="Title snapshot of the idea")
    tags: List[str] = Field(default_factory=list, description="Tags at time of saving")

# Metadata wrapper for created/updated timestamps (auto added by helper)
class Timestamped(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
