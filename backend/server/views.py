from datetime import datetime
from typing import Optional
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from .models import Server
from account.auth import APIKeyAuth

api = Router(tags=["Server"], auth=APIKeyAuth())

class ServerSchemaIn(Schema):
    name: str
    ip_address: str
    expiration_date: datetime
    location: Optional[str] = None
    description: Optional[str] = None

class ServerSchemaOut(Schema):
    id: int
    name: str
    ip_address: str
    location: Optional[str] = None
    description: Optional[str] = None
    expiration_date: datetime
    created_at: datetime

@api.get("/servers", response=list[ServerSchemaOut])
def server_list(request):
    return Server.objects.all()

@api.post("/servers", response=ServerSchemaOut)
def create_server(request, server: ServerSchemaIn):
    return Server.objects.create(**server.model_dump(exclude_unset=True))

@api.delete("/servers/{server_id}")
def delete_server(request, server_id: int):
    server = get_object_or_404(Server, id=server_id)
    server.delete()
    return {"success": True}

@api.put("/servers/{server_id}", response=ServerSchemaOut)
def update_server(request, server_id: int, server: ServerSchemaIn):
    server_obj = get_object_or_404(Server, id=server_id)
    for attr, value in server.model_dump(exclude_unset=True).items():
        setattr(server_obj, attr, value)
    server_obj.save()
    return server_obj