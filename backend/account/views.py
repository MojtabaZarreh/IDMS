from datetime import datetime
from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, File, Form, UploadedFile
from ninja.errors import HttpError
from .models import APIKey, Profile, Permission
from .auth import APIKeyAuth
from .permission import role_required

api = Router(tags=["Account"]) 

class LoginSchema(Schema):
    username: str
    password: str

class APIKeyOut(Schema):
    username: str
    role: str
    fullname: str
    key: str
    expires: datetime

class RegisterResponseIn(Schema):
    company: str
    email: str
    password: str
    fullname: str

class RegisterResponseOut(Schema):
    username: str
    role: str
    key: str

class ProfileSchemaOut(Schema):
    company: Optional[str] = None
    username: str
    role: str
    email: str
    fullname: Optional[str] = None
    city: Optional[str] = None
    logo: Optional[str] = None
    
class CreateUserSchema(Schema):
    email: str
    password: str
    fullname: str
    role: str
    
class UpdateUserProfileIn(Schema):
    fullname: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    
class UserListSchemaOut(Schema):
    username: str
    fullname: str
    role: str

@api.post("/login", response=APIKeyOut)
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    
    api_key = APIKey.create_key(user)
    return {
        "username": user.username,
        "role": user.profile.role,
        "fullname": user.profile.fullname,
        "key": api_key.key, 
        "expires": api_key.expires
    }
    
@api.post("/logout", auth=APIKeyAuth())
def logout(request):
    if APIKey.revoke_key(request.auth):
        return {"detail": "Successfully logged out."}
    raise HttpError(400, "No active API key found.")

@api.post("/register", response=RegisterResponseOut)
def register(request, data: RegisterResponseIn):
    if Profile.objects.filter(role=Permission.ADMIN).exists():
        raise HttpError(400, "Admin user already exists.")
    
    with transaction.atomic():
        user = User.objects.create_user(
            username=data.email,
            email=data.email,
            password=data.password
        )
        Profile.objects.create(
            user=user,
            role=Permission.ADMIN,
            company=data.company,
            fullname=data.fullname
        )
        api_key = APIKey.create_key(user)
        
    return {
        "username": user.username,
        "role": user.profile.role,
        "key": api_key.key
    }

@api.get("/profile", auth=APIKeyAuth(), response=ProfileSchemaOut)
def profile(request):
    profile_obj = request.auth.profile
    admin_profile = profile_obj if profile_obj.role == Permission.ADMIN else Profile.objects.filter(role=Permission.ADMIN).first()
    
    return {
        "username": profile_obj.user.username,
        "fullname": profile_obj.fullname,
        "email": profile_obj.user.email,
        "role": profile_obj.role,
        "company": admin_profile.company if admin_profile else None,
        "city": admin_profile.city if admin_profile else None,
        "logo": admin_profile.logo.url if admin_profile and admin_profile.logo else None,
    }

@api.put("/profile/admin", auth=APIKeyAuth())
@role_required('admin')
def update_profile(
    request,
    email: Optional[str] = Form(None),
    fullname: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    company: Optional[str] = Form(None), 
    city: Optional[str] = Form(None), 
    logo: Optional[UploadedFile] = File(None)
):
    profile_obj = request.auth.profile
    user = profile_obj.user
    
    if email is not None:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise HttpError(400, "Email already exists.")
        user.email = email
        user.username = email
    if fullname is not None:
        profile_obj.fullname = fullname
    if password is not None:
        user.set_password(password)
    if company is not None:
        profile_obj.company = company
    if city is not None:
        profile_obj.city = city
    if logo is not None:
        profile_obj.logo.save(logo.name, logo, save=False)
        
    user.save()
    profile_obj.save()
    return {"detail": "Profile updated successfully."}

@api.post("/create-user", auth=APIKeyAuth())
@role_required('admin')
def create_user(request, data: CreateUserSchema):
    if data.role not in [Permission.VIEWER, Permission.EDITOR]:
        raise HttpError(400, "Invalid role provided.")
        
    if User.objects.filter(username=data.email).exists():
        raise HttpError(400, "User with this email already exists.")
    
    with transaction.atomic():
        user = User.objects.create_user(
            username=data.email,
            email=data.email,
            password=data.password
        )
        Profile.objects.create(
            user=user,
            role=data.role,
            fullname=data.fullname
        )
    return {"detail": "User created successfully."}

@api.put("/profile/user", auth=APIKeyAuth())
@role_required('viewer')
def update_user_profile(request, data: UpdateUserProfileIn):
    profile_obj = request.auth.profile
    user = profile_obj.user
    
    if data.fullname is not None:
        profile_obj.fullname = data.fullname
    if data.email is not None:
        if User.objects.filter(email=data.email).exclude(id=user.id).exists():
            raise HttpError(400, "Email already exists.")
        user.email = data.email
        user.username = data.email
    if data.password is not None:
        user.set_password(data.password)

    user.save()
    profile_obj.save()
    return {"detail": "User profile updated successfully."}

@api.put("/change-role/{target_user}", auth=APIKeyAuth())
@role_required('admin')
def change_role(request, target_user: str, new_role: str):
    if new_role not in [Permission.VIEWER, Permission.EDITOR]:
        raise HttpError(400, "Invalid role provided.")
        
    user = get_object_or_404(User, username=target_user)
    profile_obj = user.profile
    profile_obj.role = new_role
    profile_obj.save()  
    return {"detail": f"Role for {user.username} updated to {new_role}."}

@api.get("/users", auth=APIKeyAuth(), response=list[UserListSchemaOut])
@role_required('viewer')
def list_users(request):
    return [
        {
            "username": user.username,
            "fullname": user.profile.fullname,
            "role": user.profile.role
        }
        for user in User.objects.select_related('profile').filter(profile__isnull=False)
    ]

@api.delete("/delete-user/{target_user}", auth=APIKeyAuth())
@role_required('admin')
def delete_user(request, target_user: str):
    user = get_object_or_404(User, username=target_user)
    user.delete()
    return {"detail": "User successfully deleted."}