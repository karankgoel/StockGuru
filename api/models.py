from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class WatchlistBase(BaseModel):
    symbol: str

class WatchlistItem(WatchlistBase):
    user_id: str

class ChatMessage(BaseModel):
    message: str
