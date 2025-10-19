from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
from bson import ObjectId

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["MSME_DATA"]           # Database
buyers_collection = db["Buyer"]   # Collection for buyers
suppliers_collection = db["Supplier"]  # Collection for suppliers/MSMEs

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def insert_buyer(data):
    """
    Inserts a new buyer from signup form.
    data = {
        "fullname": ...,
        "username": ...,
        "email": ...,
        "phone": ...,
        "password": ...,
        "buyerCompany": ...,
        "crn": ...,
        "buyerType": ...,
        "buyerIndustry": ...,
        "buyerWebsite": ...,
        "location": {
            "state": ...,
            "district": ...,
            "city": ...,
            "pincode": ...
        },
        "created_at": ...
    }
    """
    # Hash the password
    data["password"] = generate_password_hash(data["password"])
    
    # Merge location fields
    if "buyerState" in data and "buyerCity" in data and "buyerPincode" in data:
        data["location"] = {
            "state": data.pop("buyerState"),
            "city": data.pop("buyerCity"),
            "pincode": data.pop("buyerPincode")
        }
        # Add district if available
        if "buyerDistrict" in data:
            data["location"]["district"] = data.pop("buyerDistrict")
    
    data["created_at"] = datetime.utcnow()
    try:
        result = buyers_collection.insert_one(data)
        return {"success": True, "message": "Buyer account created successfully", "user_id": str(result.inserted_id)}
    except Exception as e:
        return {"success": False, "message": f"Error creating buyer account: {str(e)}"}

def insert_supplier(data):
    """
    Inserts a new supplier/MSME from signup form.
    data = {
        "fullname": ...,
        "username": ...,
        "email": ...,
        "phone": ...,
        "password": ...,
        "registrationNumber": ...,
        "companyName": ...,
        "businessType": ...,
        "industry": ...,
        "website": ...,
        "location": {
            "state": ...,
            "district": ...,
            "city": ...,
            "pincode": ...
        },
        "created_at": ...
    }
    """
    # Hash the password
    data["password"] = generate_password_hash(data["password"])
    
    # Merge location fields
    if "state" in data and "city" in data and "pincode" in data:
        data["location"] = {
            "state": data.pop("state"),
            "city": data.pop("city"),
            "pincode": data.pop("pincode")
        }
        # Add district if available
        if "district" in data:
            data["location"]["district"] = data.pop("district")
    
    data["created_at"] = datetime.utcnow()
    try:
        result = suppliers_collection.insert_one(data)
        return {"success": True, "message": "Supplier account created successfully", "user_id": str(result.inserted_id)}
    except Exception as e:
        return {"success": False, "message": f"Error creating supplier account: {str(e)}"}

def get_user_by_email(email):
    """
    Get user by email from either buyers or suppliers collection.
    Returns user data if found, None otherwise.
    """
    # Check in buyers collection first
    buyer = buyers_collection.find_one({"email": email})
    if buyer:
        buyer["role"] = "buyer"
        return buyer
    
    # Check in suppliers collection
    supplier = suppliers_collection.find_one({"email": email})
    if supplier:
        supplier["role"] = "supplier"
        return supplier
    
    return None

def verify_password(stored_password, provided_password):
    """
    Verify a password against its hash.
    """
    return check_password_hash(stored_password, provided_password)

def get_all_buyers():
    """Fetch all buyers from the collection"""
    return list(buyers_collection.find({}))

def get_all_suppliers():
    """Fetch all suppliers from the collection"""
    return list(suppliers_collection.find({}))

# Legacy function for backward compatibility
def insert_user(data):
    """
    Legacy function - routes to appropriate collection based on role.
    """
    if data.get("role") == "buyer":
        insert_buyer(data)
    elif data.get("role") == "supplier":
        insert_supplier(data)
    else:
        raise ValueError("Invalid role specified")

def get_all_msmes():
    """Legacy function - returns all suppliers"""
    return get_all_suppliers()

# JWT Functions
def generate_jwt_token(user_data):
    """
    Generate a JWT token for a user.
    user_data should contain: _id, email, username, fullname, role
    """
    payload = {
        'user_id': str(user_data['_id']),
        'email': user_data['email'],
        'username': user_data['username'],
        'fullname': user_data['fullname'],
        'role': user_data['role'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token):
    """
    Verify a JWT token and return the payload if valid.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_by_id(user_id, role):
    """
    Get user by ID from the appropriate collection.
    """
    try:
        # Convert string user_id to ObjectId
        object_id = ObjectId(user_id)
        
        if role == 'buyer':
            return buyers_collection.find_one({"_id": object_id})
        elif role == 'supplier':
            return suppliers_collection.find_one({"_id": object_id})
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    return None

def search_suppliers(filters=None):
    """
    Search suppliers based on filters.
    filters = {
        'industry': 'Manufacturing',
        'state': 'Maharashtra',
        'businessType': 'Private Limited',
        'searchTerm': 'text'
    }
    """
    query = {}
    
    if filters:
        if filters.get('industry'):
            query['industry'] = filters['industry']
        
        if filters.get('state'):
            query['location.state'] = filters['state']
        
        if filters.get('businessType'):
            query['businessType'] = filters['businessType']
        
        if filters.get('searchTerm'):
            # Text search across company name and industry
            query['$or'] = [
                {'companyName': {'$regex': filters['searchTerm'], '$options': 'i'}},
                {'industry': {'$regex': filters['searchTerm'], '$options': 'i'}}
            ]
    
    return list(suppliers_collection.find(query))

