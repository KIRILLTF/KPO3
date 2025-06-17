from pydantic import BaseModel

class AccountCreate(BaseModel):
    user_id: int

class TopUp(BaseModel):
    amount: float

class Balance(BaseModel):
    user_id: int
    balance: float
