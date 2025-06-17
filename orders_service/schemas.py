from pydantic import BaseModel

class OrderCreate(BaseModel):
    amount: float
    description: str

class Order(BaseModel):
    id: int
    user_id: int
    amount: float
    description: str
    status: str
