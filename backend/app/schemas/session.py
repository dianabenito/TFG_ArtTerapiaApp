from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionBase(BaseModel):
    start_date: datetime
    end_date: datetime
    ended_at: Optional[datetime] = None


class SessionCreate(SessionBase):
    pass


class Session(SessionBase):
    id: int
    patient_id: int
    therapist_id: int

    class Config:
        orm_mode = True
    
class SessionsOut(BaseModel):
    data: list[Session]
    count: int

class SessionUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 