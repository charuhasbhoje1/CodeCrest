# Integrated MSME Platform - Main Application
# Combines authentication system with news aggregator dashboard

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from functools import wraps
import pymongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
import requests
import plotly.graph_objs as go
import plotly.utils
import re
from collections import Counter
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database functions
from models.database import (
    insert_buyer, insert_supplier, get_user_by_email, verify_password, 
    generate_jwt_token, verify_jwt_token, get_user_by_id, search_suppliers
)

# PraisonAI imports
try:
    from praisonaiagents import Agent, PraisonAIAgents
    PRAISON_AVAILABLE = True
except ImportError:
    PRAISON_AVAILABLE = False
    print("Warning: PraisonAI not installed. Install with: pip install praisonaiagents")

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    NEWS_API_KEY = "pub_cc5d17e2d12947c081d831c461f07edd"
    DB_NAME = "news_aggregator"
    NEWS_BASE_URL = "https://newsdata.io/api/1"
    BASE_DIR = Path(__file__).resolve().parent
    PRAISON_CONFIG_PATH = BASE_DIR / "praison_agents_config.yaml"

# ==============================================================================
# FLASK APPLICATION SETUP
# ==============================================================================

app = Flask(__name__, template_folder='templates')
app.secret_key = "your_super_secret_key"
CORS(app)

# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
news_collection = db["news"]
msme_companies_collection = db["msme_companies"]

# ==============================================================================
# JWT AUTHENTICATION DECORATOR
# ==============================================================================

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        # Check for token in cookies
        if not token:
            token = request.cookies.get('jwt_token')
        
        # Check for token in session (fallback)
        if not token:
            token = session.get('jwt_token')
        
        if not token:
            print(f"DEBUG: No JWT token found. Redirecting to signin. Request path: {request.path}")
            if request.is_json:
                return jsonify({'message': 'Token is missing'}), 401
            else:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('signin'))
        
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            if payload is None:
                if request.is_json:
                    return jsonify({'message': 'Token is invalid or expired'}), 401
                else:
                    flash('Session expired. Please log in again.', 'error')
                    return redirect(url_for('signin'))
            
            # Add user info to request context
            request.current_user = payload
            
        except Exception as e:
            if request.is_json:
                return jsonify({'message': 'Token is invalid'}), 401
            else:
                flash('Authentication failed. Please log in again.', 'error')
                return redirect(url_for('signin'))
        
        return f(*args, **kwargs)
    return decorated

# ==============================================================================
# PRAISONAI AGENT SYSTEM
# ==============================================================================

class PraisonAIManager:
    def __init__(self):
        self.agents = {}
        self.initialized = False
        
    def initialize_agents(self):
        """Initialize PraisonAI agents based on configuration"""
        if not PRAISON_AVAILABLE:
            print("PraisonAI not available. Using fallback system.")
            return False
            
        try:
            self.agents = {
                'financial_analyst': Agent(
                    instructions="""You are a Financial Analyst specializing in MSME financial analysis and performance evaluation.

Your role is to:
- Analyze financial data and calculate key ratios (ROA, ROE, profit margins, debt-to-equity)
- Provide financial health scores and performance benchmarking
- Identify financial strengths, weaknesses, and improvement opportunities
- Generate financial reports with actionable insights

Always provide:
- Financial health score (0-100)
- Key performance indicators
- Comparative analysis against industry benchmarks
- Specific recommendations for financial improvement
- Risk assessment and mitigation strategies"""
                ),
                
                'news_analyst': Agent(
                    instructions="""You are a News Analyst specializing in MSME-relevant news analysis and market intelligence.

Your role is to:
- Analyze news articles for MSME relevance and impact
- Perform sentiment analysis on market trends
- Identify policy changes affecting MSMEs
- Monitor sector-specific developments and opportunities

Always provide:
- News relevance score (0-100)
- Sentiment analysis (positive/negative/neutral)
- Key insights and implications
- Sector-specific impact assessment
- Actionable recommendations based on news trends"""
                ),
                
                'company_matcher': Agent(
                    instructions="""You are a Company Matching Specialist for MSME business development.

Your role is to:
- Match companies based on business requirements and capabilities
- Analyze sector compatibility and growth potential
- Provide strategic partnership recommendations
- Assess market opportunities and competitive advantages

Always provide:
- Compatibility score (0-100)
- Match rationale and business case
- Partnership potential assessment
- Strategic recommendations
- Risk and opportunity analysis"""
                )
            }
            
            self.initialized = True
            print("PraisonAI agents initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Error initializing PraisonAI agents: {e}")
            return False

# Initialize PraisonAI manager
praison_manager = PraisonAIManager()
praison_manager.initialize_agents()

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get basic user information
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')

        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('Email already registered! Please use a different email.', 'error')
            return render_template('signup.html')

        # Create base user data
        user_data = {
            "fullname": fullname,
            "username": username,
            "email": email,
            "phone": phone,
            "password": password,
            "role": role
        }

        try:
            if role == 'buyer':
                # Collect buyer-specific data
                user_data.update({
                    "buyerCompany": request.form.get('buyerCompany'),
                    "crn": request.form.get('buyerRegistrationNumber'),
                    "buyerType": request.form.get('buyertype'),
                    "buyerIndustry": request.form.get('buyerIndustry'),
                    "buyerWebsite": request.form.get('buyerWebsite'),
                    "buyerAddress": request.form.get('buyerAddress'),
                    "buyerCity": request.form.get('buyerCity'),
                    "buyerState": request.form.get('buyerState'),
                    "buyerPincode": request.form.get('buyerPincode'),
                    "buyerCountry": request.form.get('buyerCountry')
                })
                
                # Insert buyer into database
                result = insert_buyer(user_data)
                if result and result.get('success'):
                    flash('Buyer account created successfully! Please sign in.', 'success')
                    return redirect(url_for('signin'))
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'Database operation failed'
                    flash(f'Error creating buyer account: {error_msg}', 'error')
                    
            elif role == 'supplier':
                # Collect supplier-specific data
                user_data.update({
                    "companyName": request.form.get('companyName'),
                    "registrationNumber": request.form.get('registrationNumber'),
                    "businessType": request.form.get('businessType'),
                    "industry": request.form.get('industry'),
                    "website": request.form.get('website'),
                    "address": request.form.get('address'),
                    "city": request.form.get('city'),
                    "state": request.form.get('state'),
                    "pincode": request.form.get('pincode'),
                    "country": request.form.get('country')
                })
                
                # Insert supplier into database
                result = insert_supplier(user_data)
                if result and result.get('success'):
                    flash('Supplier account created successfully! Please sign in.', 'success')
                    return redirect(url_for('signin'))
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'Database operation failed'
                    flash(f'Error creating supplier account: {error_msg}', 'error')
            
            return render_template('signup.html')
            
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Get user from database
        user = get_user_by_email(email)
        if user and verify_password(user['password'], password):
            # Generate JWT token
            token = generate_jwt_token(user)
            
            # Store token in session
            session['jwt_token'] = token
            session['user_id'] = str(user['_id'])
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            # Redirect based on role
            if user['role'] == 'buyer':
                return redirect(url_for('buyer_dashboard'))
            elif user['role'] == 'supplier':
                return redirect(url_for('supplier_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

# ==============================================================================
# DASHBOARD ROUTES
# ==============================================================================

@app.route('/buyer')
@jwt_required
def buyer_dashboard():
    user_id = request.current_user['user_id']
    user_role = request.current_user['role']
    user_data = get_user_by_id(user_id, user_role)
    return render_template('buyer.html', user_data=user_data)

@app.route('/supplier')
@jwt_required
def supplier_dashboard():
    user_id = request.current_user['user_id']
    user_role = request.current_user['role']
    user_data = get_user_by_id(user_id, user_role)
    return render_template('buyer.html', user_data=user_data)  # Using same template for now

@app.route('/profile')
@jwt_required
def profile():
    user_id = request.current_user['user_id']
    user_role = request.current_user['role']
    user_data = get_user_by_id(user_id, user_role)
    return render_template('profile.html', user_data=user_data)

@app.route('/marketplace')
# @jwt_required  # Temporarily disabled for testing
def marketplace():
    return render_template('msme_directory_enhanced_search.html')

@app.route('/dashboard')
# @jwt_required  # Temporarily disabled for testing
def news_dashboard():
    return render_template('index.html')

@app.route('/news')
# @jwt_required  # Temporarily disabled for testing
def news():
    """News page with API integration"""
    return render_template('news_new.html')

# ==============================================================================
# API ROUTES FOR NEWS AND ANALYTICS
# ==============================================================================

@app.route('/api/praison-status', methods=['GET'])
def praison_status():
    """Check PraisonAI system status"""
    return jsonify({
        'praison_available': PRAISON_AVAILABLE,
        'agents_initialized': praison_manager.initialized,
        'agents_count': len(praison_manager.agents) if praison_manager.initialized else 0
    })

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """Load MSME data from CSV files"""
    try:
        # Load MSME companies data
        msme_file = Config.BASE_DIR / "MSME_32hai.csv"
        if msme_file.exists():
            df_msme = pd.read_csv(msme_file)
            msme_data = df_msme.to_dict('records')
            
            # Clear existing data
            msme_companies_collection.delete_many({})
            
            # Insert new data
            if msme_data:
                msme_companies_collection.insert_many(msme_data)
            
            return jsonify({
                'success': True,
                'message': f'Loaded {len(msme_data)} MSME companies',
                'count': len(msme_data)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'MSME data file not found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/dashboard/companies', methods=['GET'])
def get_companies():
    """Get MSME companies for dashboard"""
    try:
        companies = list(msme_companies_collection.find({}, {'_id': 0}))
        return jsonify({
            'success': True,
            'companies': companies,
            'count': len(companies)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/fetch-news', methods=['POST'])
def fetch_news():
    """Fetch news articles from NewsData.io API"""
    try:
        data = request.get_json()
        query = data.get('query', 'MSME')
        
        print(f"DEBUG: Fetching news with query: {query}")
        print(f"DEBUG: Using API key: {Config.NEWS_API_KEY[:10]}...")
        
        # NewsData.io API call
        url = f"{Config.NEWS_BASE_URL}/news"
        params = {
            'apikey': Config.NEWS_API_KEY,
            'q': query,
            'language': 'en',
            'country': 'in',
            'category': 'business'
        }
        
        print(f"DEBUG: Making request to: {url}")
        print(f"DEBUG: Params: {params}")
        
        response = requests.get(url, params=params)
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get('results', [])
            print(f"DEBUG: Found {len(articles)} articles")
            
            # Store in database
            stored_articles = []
            for article in articles:
                article['fetched_at'] = datetime.now()
                result = news_collection.insert_one(article)
                # Convert ObjectId to string for JSON response
                article['_id'] = str(result.inserted_id)
                article['fetched_at'] = article['fetched_at'].isoformat()
                stored_articles.append(article)
            
            print(f"DEBUG: Stored {len(stored_articles)} articles in database")
            
            return jsonify({
                'success': True,
                'articles': stored_articles,
                'count': len(stored_articles)
            })
        else:
            print(f"DEBUG: API request failed with status {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")
            return jsonify({
                'success': False,
                'error': f'API request failed: {response.status_code} - {response.text}'
            })
            
    except Exception as e:
        print(f"DEBUG: Exception in fetch_news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/latest-news', methods=['GET'])
def get_latest_news():
    """Get latest news articles from database"""
    try:
        # Get latest 10 articles
        articles = list(news_collection.find().sort('fetched_at', -1).limit(10))
        print(f"DEBUG: Found {len(articles)} articles in database")
        
        # Convert ObjectId to string for JSON serialization
        for article in articles:
            article['_id'] = str(article['_id'])
            if 'fetched_at' in article:
                article['fetched_at'] = article['fetched_at'].isoformat()
        
        print(f"DEBUG: Returning {len(articles)} articles")
        
        return jsonify({
            'success': True,
            'articles': articles,
            'count': len(articles)
        })
    except Exception as e:
        print(f"DEBUG: Exception in get_latest_news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/dashboard/filters', methods=['GET'])
def get_dashboard_filters():
    """Get filter options for dashboard"""
    try:
        # Extract unique values from companies
        companies_cursor = msme_companies_collection.find({})
        companies = list(companies_cursor)
        
        locations = list(set(c.get('Location', '') for c in companies if c.get('Location')))
        sectors = list(set(c.get('Sector', '') for c in companies if c.get('Sector')))
        export_markets = []
        for c in companies:
            markets = c.get('Export_Markets', '')
            if markets:
                export_markets.extend([m.strip() for m in markets.split(',')])
        export_markets = list(set(export_markets))
        
        return jsonify({
            'success': True,
            'filters': {
                'locations': sorted(locations),
                'sectors': sorted(sectors),
                'export_markets': sorted(export_markets)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-json', methods=['GET'])
def test_json():
    """Test JSON response for debugging"""
    try:
        companies = list(msme_companies_collection.find({}, {'_id': 0}).limit(1))
        if companies:
            # Test if we can serialize the first company
            import json
            test_data = {
                'success': True,
                'test_company': companies[0],
                'count': len(companies)
            }
            # This will fail if there are NaN values
            json_str = json.dumps(test_data)
            return jsonify(test_data)
        else:
            return jsonify({'success': False, 'error': 'No companies found'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'JSON serialization failed: {str(e)}'})

# ==============================================================================
# API ROUTES FOR AUTHENTICATION
# ==============================================================================

@app.route('/api/verify-token', methods=['GET'])
def verify_token():
    """Verify JWT token"""
    token = request.cookies.get('jwt_token') or session.get('jwt_token')
    if token:
        payload = verify_jwt_token(token)
        if payload:
            return jsonify({'valid': True, 'user': payload})
    return jsonify({'valid': False})

@app.route('/api/current-user', methods=['GET'])
@jwt_required
def current_user():
    """Get current user information"""
    user_id = request.current_user['user_id']
    user_role = request.current_user['role']
    user_data = get_user_by_id(user_id, user_role)
    if user_data:
        user_data['_id'] = str(user_data['_id'])
        user_data.pop('password', None)  # Remove password from response
    return jsonify(user_data)

@app.route('/api/refresh-token', methods=['POST'])
@jwt_required
def refresh_token():
    """Refresh JWT token"""
    user_id = request.current_user['user_id']
    user_role = request.current_user['role']
    
    # Get user data to generate new token
    user_data = get_user_by_id(user_id, user_role)
    if user_data:
        new_token = generate_jwt_token(user_data)
        session['jwt_token'] = new_token
        return jsonify({'success': True, 'token': new_token})
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404

# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('homepage.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==============================================================================
# APPLICATION RUNNER
# ==============================================================================

if __name__ == '__main__':
    print("Starting Integrated MSME Platform...")
    print(f"PraisonAI Available: {PRAISON_AVAILABLE}")
    print(f"Agents Initialized: {praison_manager.initialized}")
    
    # Load initial data
    try:
        print("Loading MSME data...")
        # This will be called when the API endpoint is hit
    except Exception as e:
        print(f"Warning: Could not load initial data: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
