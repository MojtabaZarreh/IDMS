from datetime import datetime, date
from typing import Optional
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from .models import Domain, DomainAction
from account.auth import APIKeyAuth
from account.permission import role_required

api = Router(tags=["Domain"], auth=APIKeyAuth())

class DomainSchemaIn(Schema):
    name: str
    register: str
    status: str
    expiration_date: date
    description: Optional[str] = None

class DomainSchemaOut(Schema):
    id: int
    name: str
    register: str
    status: str
    expiration_date: date
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DomainActionSchemaIn(Schema):
    description: str

class DomainActionSchemaOut(Schema):
    id: int
    description: str
    created_at: datetime
    
@api.get("/domains", response=list[DomainSchemaOut])
@role_required('viewer')
def domain_list(request):
    return Domain.objects.all()

@api.post("/domains", response=DomainSchemaOut)
@role_required('viewer')
def create_domain(request, domain: DomainSchemaIn):
    return Domain.objects.create(**domain.model_dump(exclude_unset=True))

@api.delete("/domains/{domain_id}")
def delete_domain(request, domain_id: int):
    domain = get_object_or_404(Domain, id=domain_id)
    domain.delete()
    return {"success": True}

@api.put("/domains/{domain_id}", response=DomainSchemaOut)
def update_domain(request, domain_id: int, domain: DomainSchemaIn):
    domain_obj = get_object_or_404(Domain, id=domain_id)
    for attr, value in domain.model_dump(exclude_unset=True).items():
        setattr(domain_obj, attr, value)
    domain_obj.save()
    return domain_obj

@api.get("/domains/{domain_id}/actions", response=list[DomainActionSchemaOut])
def domain_actions(request, domain_id: int):
    get_object_or_404(Domain, id=domain_id)
    return DomainAction.objects.filter(domain_id=domain_id)
    
@api.post("/domains/{domain_id}/actions", response=DomainActionSchemaOut)
def create_domain_action(request, domain_id: int, action: DomainActionSchemaIn):
    domain = get_object_or_404(Domain, id=domain_id)
    return DomainAction.objects.create(
        domain=domain,
        description=action.description
    )