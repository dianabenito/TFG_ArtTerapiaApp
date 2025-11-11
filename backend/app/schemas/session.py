from pydantic import BaseModel

class SessionBase(BaseModel):
    pass

class SessionCreate(SessionBase):
    pass

class Session(BaseModel):
    id: int
    patient_id: int
    therapist_id: int
    class Config:
        orm_mode = True
    