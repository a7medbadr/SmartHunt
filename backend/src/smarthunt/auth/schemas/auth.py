from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    # الأسلوب الحديث والمدعوم في Pydantic v2 لتجنب تحذيرات الـ Deprecation
    model_config = ConfigDict(from_attributes=True)
