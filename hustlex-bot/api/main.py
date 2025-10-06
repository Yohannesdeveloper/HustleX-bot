# api/main.py
import os, hashlib, hmac, urllib.parse, re
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
from typing import Optional

app = FastAPI()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003194542999")

def verify_init_data(init_data_str: str, bot_token: str) -> bool:
    # init_data_str is the raw query-like string Telegram sends (contains hash param)
    params = dict(urllib.parse.parse_qsl(init_data_str, keep_blank_values=True))
    hash_received = params.pop("hash", None)
    if not hash_received:
        return False
    data_check_list = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_check_list)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac_hash == hash_received

@app.post("/api/profile")
async def save_profile(
    name: str = Form(...),
    age: int = Form(...),
    sex: str = Form(...),
    contact_info: str = Form(None),
    cv_file: UploadFile = File(None),
    profile_pic: UploadFile = File(None),
    init_data: str = Form(...)
):
    # Verify the init_data
    if not verify_init_data(init_data, BOT_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid initData")
    
    # Process the profile data
    profile_data = {
        "name": name,
        "age": age,
        "sex": sex,
    }
    
    # Add contact info if provided
    if contact_info:
        profile_data["contact_info"] = contact_info
    
    # Handle CV file if provided
    if cv_file:
        # Save the CV file
        file_path = f"uploads/cv/{cv_file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(await cv_file.read())
        
        profile_data["cv_file_path"] = file_path
    
    # Handle profile picture if provided
    if profile_pic:
        # Save the profile picture
        pic_path = f"uploads/profile_pics/{profile_pic.filename}"
        os.makedirs(os.path.dirname(pic_path), exist_ok=True)
        
        with open(pic_path, "wb") as f:
            f.write(await profile_pic.read())
        
        profile_data["profile_pic_file_path"] = pic_path
    
    # TODO: Save profile_data to database
    
    return {"status": "success", "message": "Profile saved successfully"}
