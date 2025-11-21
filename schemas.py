"""
Database Schemas for FocusSync

Each Pydantic model corresponds to a MongoDB collection. Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Userprofile(BaseModel):
    """
    Users of FocusSync
    Collection: "userprofile"
    """
    name: str = Field(..., description="Display name")
    email: Optional[str] = Field(None, description="Email (optional)")
    avatar: Optional[str] = Field(None, description="Avatar URL")

class Queueentry(BaseModel):
    """
    Waiting room entries for matchmaking
    Collection: "queueentry"
    """
    user_name: str = Field(..., description="User's display name")
    focus_topic: Optional[str] = Field(None, description="Optional topic or goal for the session")
    timezone: Optional[str] = Field(None, description="User timezone")

class Focussession(BaseModel):
    """
    Active or completed deep work sessions
    Collection: "focussession"
    """
    participant_names: List[str] = Field(..., description="Two participant display names")
    started_at: datetime = Field(..., description="Session start time (UTC)")
    duration_minutes: int = Field(50, ge=15, le=120, description="Planned duration in minutes")
    status: str = Field("active", description="active|ended|cancelled")
    focus_topic: Optional[str] = Field(None, description="Optional shared topic")
