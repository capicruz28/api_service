from pydantic import BaseModel

class TokenData(BaseModel):
    username: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_data: dict

class LoginData(BaseModel):
    username: str
    password: str