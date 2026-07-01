import requests
import urllib3
from datetime import datetime
from typing import Optional
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Schema
from .models import Website
from account.auth import APIKeyAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api = Router(tags=["Website"], auth=APIKeyAuth())

class WebsiteSchemaIn(Schema):
    url: str
    description: Optional[str] = None

class WebsiteSchemaOut(Schema):
    id: int
    url: str
    status: str
    description: Optional[str] = None
    last_checked: Optional[datetime] = None
    created_at: datetime

def check_website_status(url: str) -> tuple[str, str]:
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    try:
        response = requests.get(url, timeout=5, verify=False)
        return url, "up" if response.ok else "down"
    except requests.RequestException:
        return url, "down"

@api.get("/websites", response=list[WebsiteSchemaOut])
def website_list(request):
    return Website.objects.all()

@api.post("/websites", response=WebsiteSchemaOut)
def create_website(request, data: WebsiteSchemaIn):
    url, status = check_website_status(data.url)
    return Website.objects.create(
        url=url, 
        description=data.description, 
        status=status
    )

@api.delete("/websites/{website_id}")
def delete_website(request, website_id: int):
    website = get_object_or_404(Website, id=website_id)
    website.delete()
    return {"success": True}

@api.put("/websites/{website_id}", response=WebsiteSchemaOut)
def update_website(request, website_id: int):
    website = get_object_or_404(Website, id=website_id)
    _, status = check_website_status(website.url)
    
    website.status = status
    website.last_checked = timezone.now()
    website.save()
    
    return website