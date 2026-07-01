from typing import Optional
from datetime import datetime
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from password.models import Password
from account.auth import APIKeyAuth

api = Router(tags=["Password"], auth=APIKeyAuth())

class PasswordSchemaIn(Schema):
    label: str
    username: str
    password: str
    url: Optional[str] = None
    notes: Optional[str] = None

class PasswordSchemaOut(Schema):
    id: int
    label: str
    username: str
    password: str
    url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@api.get("/passwords", response=list[PasswordSchemaOut])
def password_list(request):
    return Password.objects.all()

@api.post("/passwords", response=PasswordSchemaOut)
def create_password(request, password: PasswordSchemaIn):
    return Password.objects.create(**password.model_dump(exclude_unset=True))

@api.put("/passwords/{password_id}", response=PasswordSchemaOut)
def update_password(request, password_id: int, password: PasswordSchemaIn):
    pwd = get_object_or_404(Password, id=password_id)
    for attr, value in password.model_dump(exclude_unset=True).items():
        setattr(pwd, attr, value)
    pwd.save()
    return pwd

@api.delete("/passwords/{password_id}")
def delete_password(request, password_id: int):
    pwd = get_object_or_404(Password, id=password_id)
    pwd.delete()
    return {"success": True}