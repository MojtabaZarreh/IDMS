from typing import Optional, List
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, UploadedFile, Form, File
from .models import FinancialRecord
from account.auth import APIKeyAuth

api = Router(tags=["Financial"], auth=APIKeyAuth())

class FinancialRecordSchemaOut(Schema):
    id: int
    subject: str
    record_date: str
    description: Optional[str] = None
    attachment: Optional[List[str]] = None

@api.get("/financial-records", response=list[FinancialRecordSchemaOut])
def financial_record_list(request):
    return FinancialRecord.objects.all()

@api.post("/financial-records", response=FinancialRecordSchemaOut)
def create_financial_record(
    request,
    subject: str = Form(...),
    record_date: str = Form(...),
    description: Optional[str] = Form(None),
    files: Optional[List[UploadedFile]] = File(None)
):
    file_urls = []
    if files:
        fs = FileSystemStorage(location='media/docs/', base_url='/media/docs/')
        file_urls = [fs.url(fs.save(f.name, f)) for f in files]

    return FinancialRecord.objects.create(
        subject=subject,
        record_date=record_date,
        description=description,
        attachment=file_urls if file_urls else None
    )

@api.delete("/financial-records/{record_id}")
def delete_financial_record(request, record_id: int):
    record = get_object_or_404(FinancialRecord, id=record_id)
    record.delete()
    return {"success": True}

@api.put("/financial-records/{record_id}", response=FinancialRecordSchemaOut)
def update_financial_record(
    request,
    record_id: int,
    subject: Optional[str] = Form(None),
    record_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    files: Optional[List[UploadedFile]] = File(None)
):
    record = get_object_or_404(FinancialRecord, id=record_id)
    
    if subject is not None:
        record.subject = subject
    if record_date is not None:
        record.record_date = record_date
    if description is not None:
        record.description = description
    if files:
        fs = FileSystemStorage(location='media/docs/', base_url='/media/docs/')
        new_urls = [fs.url(fs.save(f.name, f)) for f in files]
        current_attachments = record.attachment if isinstance(record.attachment, list) else []
        record.attachment = current_attachments + new_urls
        
    record.save()
    return record