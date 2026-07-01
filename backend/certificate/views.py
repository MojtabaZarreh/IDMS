from datetime import datetime, date
from typing import Optional
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from .models import Certificate
from account.auth import APIKeyAuth

api = Router(tags=["Certificate"], auth=APIKeyAuth())

class CertificateSchemaIn(Schema):
    name: str
    issuer: str
    expiration_date: date
    description: Optional[str] = None

class CertificateSchemaOut(Schema):
    id: int
    name: str
    issuer: str
    expiration_date: date
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@api.get("/ssl", response=list[CertificateSchemaOut])
def certificate_list(request):
    return Certificate.objects.all()

@api.post("/ssl", response=CertificateSchemaOut)
def create_certificate(request, certificate: CertificateSchemaIn):
    return Certificate.objects.create(**certificate.model_dump(exclude_unset=True))

@api.delete("/ssl/{certificate_id}")
def delete_certificate(request, certificate_id: int):
    cert = get_object_or_404(Certificate, id=certificate_id)
    cert.delete()
    return {"success": True}

@api.put("/ssl/{certificate_id}", response=CertificateSchemaOut)
def update_certificate(request, certificate_id: int, certificate: CertificateSchemaIn):
    cert = get_object_or_404(Certificate, id=certificate_id)
    for attr, value in certificate.model_dump(exclude_unset=True).items():
        setattr(cert, attr, value)
    cert.save()
    return cert