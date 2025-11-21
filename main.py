import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from database import db, create_document, get_documents
from schemas import Queueentry, Focussession, Userprofile

app = FastAPI(title="FocusSync API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FocusSync backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Request models for API
class JoinQueueRequest(BaseModel):
    user_name: str
    focus_topic: Optional[str] = None
    timezone: Optional[str] = None

class MatchResponse(BaseModel):
    matched: bool
    session_id: Optional[str] = None

@app.post("/queue/join", response_model=MatchResponse)
def join_queue(payload: JoinQueueRequest):
    # Store entry
    entry = Queueentry(user_name=payload.user_name, focus_topic=payload.focus_topic, timezone=payload.timezone)
    create_document("queueentry", entry)

    # Simple matchmaking: find another waiting entry with different name
    waiting = get_documents("queueentry", {"user_name": {"$ne": payload.user_name}}, limit=1)
    if waiting:
        partner = waiting[0]
        # Create session
        session = Focussession(
            participant_names=[payload.user_name, partner.get("user_name", "Partner")],
            started_at=datetime.now(timezone.utc),
            duration_minutes=50,
            status="active",
            focus_topic=payload.focus_topic or partner.get("focus_topic")
        )
        session_id = create_document("focussession", session)
        return MatchResponse(matched=True, session_id=session_id)

    return MatchResponse(matched=False)

class EndSessionRequest(BaseModel):
    session_id: str

@app.post("/session/end")
def end_session(req: EndSessionRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    from bson import ObjectId
    try:
        db["focussession"].update_one({"_id": ObjectId(req.session_id)}, {"$set": {"status": "ended", "updated_at": datetime.now(timezone.utc)}})
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Minimal signaling placeholder (non-functional, to be replaced by real signaling later)
class SignalingTokenResponse(BaseModel):
    token: str

@app.get("/signaling/token", response_model=SignalingTokenResponse)
def get_signaling_token():
    # In production you'd issue a real token from a provider (e.g., LiveKit, Daily, Twilio)
    return SignalingTokenResponse(token="demo-token")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
