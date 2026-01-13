import os
from supabase import create_client, Client
from .config import Config

def get_supabase_client() -> Client:
    url = Config.SUPABASE_URL
    secret_key = Config.SECRET_KEY  
    if not url or not secret_key:
        return None
    return create_client(url, secret_key)

supabase: Client = get_supabase_client()
