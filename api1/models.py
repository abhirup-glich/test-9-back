from .utils import supabase
from datetime import datetime

class UserModel:
    TABLE_NAME = 'students'

    @staticmethod
    def create(data):
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        data['created_at'] = datetime.utcnow().isoformat()
        response = supabase.table(UserModel.TABLE_NAME).insert(data).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def get_by_email(email):
        if not supabase:
            return None
        response = supabase.table(UserModel.TABLE_NAME).select("*").eq("email", email).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def get_by_id(user_id):
        if not supabase:
            return None
        response = supabase.table(UserModel.TABLE_NAME).select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_roll_number(roll_number):
        if not supabase:
            return None
        response = supabase.table(UserModel.TABLE_NAME).select("*").eq("roll_number", roll_number).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def update_password(user_id, new_password):
        if not supabase:
            raise Exception("Supabase client not initialized")
        response = supabase.table(UserModel.TABLE_NAME).update({"password": new_password}).eq("id", user_id).execute()
        return response.data
