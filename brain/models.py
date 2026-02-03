from pydantic import BaseModel

class TrustEvent(BaseModel):
    event_id: str
    actor: str
    action: str
    payload: str
