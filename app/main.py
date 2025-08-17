from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from app.routers._for_admin_ import admin_router

from app.middleware_token import BearerAuthASGIMiddleware
from app.security import creds, create_access_token, verify_access_token
from typing import Optional
from fastapi import Header
import pandas as pd
import json
import uuid
from datetime import datetime, timedelta
import os


app = FastAPI(
    title="Dashboard Service",
    description="A dashboard service for managing donations and users.",
    version="0.0.1"
)

app.add_middleware(BearerAuthASGIMiddleware)

origins = [
    "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    """
    Generate the custom OpenAPI schema for the secret-vault-service API.

    :return: The OpenAPI schema.
    """

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="dashboard-service",
        description="API for the dashboard service",
        version="0.0.1",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(admin_router)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 60 * 30  


@app.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if not creds.verify_password(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(sub=body.username)
    return TokenResponse(access_token=token)

@app.get("/auth/validate")
async def validate_token(authorization: Optional[str] = Header(None)):
    """Validate a bearer token and return user information."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = payload.get("sub")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {"valid": True, "user": user}

@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Upload an Excel file and convert it to JSON."""
    # Validate token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file.file)
        
        # Convert DataFrame to JSON
        json_data = df.to_dict(orient='records')
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"donations_{timestamp}_{unique_id}.json"
        
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Save JSON file
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        return {
            "message": "File uploaded successfully",
            "filename": filename,
            "records_count": len(json_data),
            "file_path": file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/list-uploads")
async def list_uploads(authorization: Optional[str] = Header(None)):
    """List all uploaded JSON files."""
    # Validate token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return {"files": []}
        
        files = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(data_dir, filename)
                file_stats = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return {"files": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/download-template")
async def download_template():
    """Download a sample Excel template for donations."""
    try:
        # Create sample data
        sample_data = {
            'Donor_Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'Email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com'],
            'Phone': ['555-0101', '555-0102', '555-0103', '555-0104'],
            'Amount': [100.00, 250.50, 75.25, 500.00],
            'Payment_Method': ['Zelle', 'Zelle', 'Zelle', 'Zelle'],
            'Transaction_ID': ['Z123456789', 'Z987654321', 'Z456789123', 'Z789123456'],
            'Date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18'],
            'Notes': ['Monthly donation', 'One-time gift', 'In memory of...', 'Campaign donation']
        }
        
        # Create DataFrame
        df = pd.DataFrame(sample_data)
        
        # Create template directory if it doesn't exist
        template_dir = "templates"
        os.makedirs(template_dir, exist_ok=True)
        
        # Save as Excel file
        template_path = os.path.join(template_dir, "donations_template.xlsx")
        df.to_excel(template_path, index=False, engine='openpyxl')
        
        # Read the file and return it
        with open(template_path, 'rb') as f:
            content = f.read()
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=donations_template.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@app.get("/dashboard-data")
async def get_dashboard_data(authorization: Optional[str] = Header(None)):
    """Get dashboard data from the latest uploaded JSON file."""
    # Validate token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return {
                "total_donations": 0,
                "total_amount": 0,
                "active_donors": 0,
                "recent_activity": [],
                "top_donors": [],
                "monthly_trend": []
            }
        
        # Get the most recent JSON file
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        if not json_files:
            return {
                "total_donations": 0,
                "total_amount": 0,
                "active_donors": 0,
                "recent_activity": [],
                "top_donors": [],
                "monthly_trend": []
            }
        
        # Sort by creation time (newest first)
        json_files.sort(key=lambda x: os.path.getctime(os.path.join(data_dir, x)), reverse=True)
        latest_file = json_files[0]
        
        # Read the JSON file
        with open(os.path.join(data_dir, latest_file), 'r') as f:
            donations_data = json.load(f)
        
        if not donations_data:
            return {
                "total_donations": 0,
                "total_amount": 0,
                "active_donors": 0,
                "recent_activity": [],
                "top_donors": [],
                "monthly_trend": []
            }
        
        # Process the data
        total_donations = len(donations_data)
        total_amount = sum(float(donation.get('Amount', 0)) for donation in donations_data)
        active_donors = len(set(donation.get('Donor_Name', '') for donation in donations_data if donation.get('Donor_Name')))
        
        # Get recent activity (last 5 donations)
        recent_activity = []
        for donation in donations_data[-5:]:
            recent_activity.append({
                "type": "donation",
                "message": f"${donation.get('Amount', 0)} from {donation.get('Donor_Name', 'Unknown')}",
                "date": donation.get('Date', ''),
                "amount": float(donation.get('Amount', 0))
            })
        
        # Get top donors
        donor_totals = {}
        for donation in donations_data:
            donor_name = donation.get('Donor_Name', 'Unknown')
            amount = float(donation.get('Amount', 0))
            donor_totals[donor_name] = donor_totals.get(donor_name, 0) + amount
        
        top_donors = sorted(donor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        top_donors = [{"name": name, "total": total} for name, total in top_donors]
        
        # Calculate monthly trend (last 6 months)
        monthly_trend = []
        for i in range(6):
            month_date = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_total = 0
            for donation in donations_data:
                try:
                    donation_date = datetime.strptime(donation.get('Date', ''), '%Y-%m-%d')
                    if donation_date.month == month_date.month and donation_date.year == month_date.year:
                        month_total += float(donation.get('Amount', 0))
                except:
                    continue
            monthly_trend.append({
                "month": month_date.strftime('%b %Y'),
                "amount": month_total
            })
        
        monthly_trend.reverse()  # Show oldest to newest
        
        return {
            "total_donations": total_donations,
            "total_amount": round(total_amount, 2),
            "active_donors": active_donors,
            "recent_activity": recent_activity,
            "top_donors": top_donors,
            "monthly_trend": monthly_trend,
            "data_source": latest_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing dashboard data: {str(e)}")

@app.get("/healthz")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def login_page():
    """
    Serve the login page HTML.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 25%, #20B2AA 50%, #48D1CC 75%, #40E0D0 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .login-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(15px);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(46, 139, 87, 0.3);
                width: 100%;
                max-width: 400px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .login-header h1 {
                color: #2E8B57;
                margin: 0;
                font-size: 2rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #2E8B57;
                font-weight: 600;
            }
            .form-group input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                font-size: 1rem;
                box-sizing: border-box;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.9);
            }
            .form-group input:focus {
                outline: none;
                border-color: #2E8B57;
                box-shadow: 0 0 0 3px rgba(46, 139, 87, 0.1);
            }
            .login-btn {
                width: 100%;
                padding: 0.75rem;
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 6px 20px rgba(46, 139, 87, 0.3);
            }
            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(46, 139, 87, 0.4);
            }
            .login-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .error-message {
                color: #e74c3c;
                text-align: center;
                margin-top: 1rem;
                display: none;
                padding: 10px;
                border-radius: 8px;
                background: rgba(231, 76, 60, 0.1);
                border: 1px solid rgba(231, 76, 60, 0.3);
            }
            .success-message {
                color: #27ae60;
                text-align: center;
                margin-top: 1rem;
                display: none;
                padding: 10px;
                border-radius: 8px;
                background: rgba(39, 174, 96, 0.1);
                border: 1px solid rgba(39, 174, 96, 0.3);
            }
            .loading-container {
                display: none;
                text-align: center;
                margin-top: 1rem;
            }
            .loading-spinner {
                width: 30px;
                height: 30px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #2E8B57;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>Dashboard Login</h1>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn" id="loginBtn">Login</button>
            </form>
            <div id="errorMessage" class="error-message"></div>
            <div id="successMessage" class="success-message"></div>
            <div id="loadingContainer" class="loading-container">
                <div class="loading-spinner"></div>
                <p>Checking authentication...</p>
            </div>
        </div>

        <script>
            // Check for existing authentication on page load
            document.addEventListener('DOMContentLoaded', function() {
                const token = localStorage.getItem('authToken');
                if (token) {
                    // Show loading state
                    document.getElementById('loadingContainer').style.display = 'block';
                    document.getElementById('loginForm').style.display = 'none';
                    
                    // Validate the existing token
                    fetch('/auth/validate', {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => {
                        if (response.ok) {
                            // Token is valid, redirect to admin portal
                            window.location.href = '/admin';
                        } else {
                            // Token is invalid, clear it and show login form
                            localStorage.removeItem('authToken');
                            document.getElementById('loadingContainer').style.display = 'none';
                            document.getElementById('loginForm').style.display = 'block';
                        }
                    })
                    .catch(error => {
                        console.error('Token validation error:', error);
                        // Error occurred, clear token and show login form
                        localStorage.removeItem('authToken');
                        document.getElementById('loadingContainer').style.display = 'none';
                        document.getElementById('loginForm').style.display = 'block';
                    });
                }
            });

            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const loginBtn = document.getElementById('loginBtn');
                const errorMessage = document.getElementById('errorMessage');
                const successMessage = document.getElementById('successMessage');
                
                // Clear previous messages
                errorMessage.style.display = 'none';
                successMessage.style.display = 'none';
                
                // Disable button and show loading state
                loginBtn.disabled = true;
                loginBtn.textContent = 'Logging in...';
                
                try {
                    // Step 1: Get bearer token
                    const loginResponse = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    });
                    
                    if (!loginResponse.ok) {
                        throw new Error('Invalid credentials');
                    }
                    
                    const tokenData = await loginResponse.json();
                    const bearerToken = tokenData.access_token;
                    
                    // Store the token for future use
                    localStorage.setItem('authToken', bearerToken);
                    
                    // Step 2: Redirect to admin page
                    window.location.href = '/admin';
                    
                } catch (error) {
                    console.error('Login error:', error);
                    errorMessage.textContent = error.message || 'Login failed. Please try again.';
                    errorMessage.style.display = 'block';
                } finally {
                    // Re-enable button
                    loginBtn.disabled = false;
                    loginBtn.textContent = 'Login';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/public-dashboard", response_class=HTMLResponse)
async def public_dashboard():
    """Public dashboard that anyone can view without authentication."""
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Donations Dashboard</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        color: #333;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        padding: 30px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .header h1 {
                        color: #333;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .header p {
                        color: #666;
                        font-size: 1.2rem;
                    }
                    .no-data {
                        text-align: center;
                        padding: 50px;
                        color: #666;
                    }
                    .no-data h2 {
                        color: #333;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Donations Dashboard</h1>
                        <p>Transparency in giving</p>
                    </div>
                    <div class="no-data">
                        <h2>No donation data available</h2>
                        <p>Check back later for updates on our donation activities.</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Get the most recent JSON file
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        if not json_files:
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Donations Dashboard</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        color: #333;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        padding: 30px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .header h1 {
                        color: #333;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .header p {
                        color: #666;
                        font-size: 1.2rem;
                    }
                    .no-data {
                        text-align: center;
                        padding: 50px;
                        color: #666;
                    }
                    .no-data h2 {
                        color: #333;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Donations Dashboard</h1>
                        <p>Transparency in giving</p>
                    </div>
                    <div class="no-data">
                        <h2>No donation data available</h2>
                        <p>Check back later for updates on our donation activities.</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Sort by creation time (newest first)
        json_files.sort(key=lambda x: os.path.getctime(os.path.join(data_dir, x)), reverse=True)
        latest_file = json_files[0]
        
        # Read the JSON file
        with open(os.path.join(data_dir, latest_file), 'r') as f:
            donations_data = json.load(f)
        
        if not donations_data:
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Donations Dashboard</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        color: #333;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        padding: 30px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .header h1 {
                        color: #333;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .header p {
                        color: #666;
                        font-size: 1.2rem;
                    }
                    .no-data {
                        text-align: center;
                        padding: 50px;
                        color: #666;
                    }
                    .no-data h2 {
                        color: #333;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Donations Dashboard</h1>
                        <p>Transparency in giving</p>
                    </div>
                    <div class="no-data">
                        <h2>No donation data available</h2>
                        <p>Check back later for updates on our donation activities.</p>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Process the data
        total_donations = len(donations_data)
        total_amount = sum(float(donation.get('Amount', 0)) for donation in donations_data)
        active_donors = len(set(donation.get('Donor_Name', '') for donation in donations_data if donation.get('Donor_Name')))
        
        # Get recent activity (last 5 donations)
        recent_activity = []
        for donation in donations_data[-5:]:
            recent_activity.append({
                "message": f"${donation.get('Amount', 0)} from {donation.get('Donor_Name', 'Anonymous')}",
                "date": donation.get('Date', ''),
                "amount": float(donation.get('Amount', 0))
            })
        
        # Get top donors
        donor_totals = {}
        for donation in donations_data:
            donor_name = donation.get('Donor_Name', 'Anonymous')
            amount = float(donation.get('Amount', 0))
            donor_totals[donor_name] = donor_totals.get(donor_name, 0) + amount
        
        top_donors = sorted(donor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        top_donors = [{"name": name, "total": total} for name, total in top_donors]
        
        # Calculate monthly trend (last 6 months)
        monthly_trend = []
        for i in range(6):
            month_date = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_total = 0
            for donation in donations_data:
                try:
                    donation_date = datetime.strptime(donation.get('Date', ''), '%Y-%m-%d')
                    if donation_date.month == month_date.month and donation_date.year == month_date.year:
                        month_total += float(donation.get('Amount', 0))
                except:
                    continue
            monthly_trend.append({
                "month": month_date.strftime('%b %Y'),
                "amount": month_total
            })
        
        monthly_trend.reverse()  # Show oldest to newest
        
        # Calculate bar heights for monthly trend
        max_amount = max([month["amount"] for month in monthly_trend]) if monthly_trend else 1
        trend_bars = []
        for month in monthly_trend:
            height = int((month["amount"] / max_amount) * 60) if max_amount > 0 else 0
            trend_bars.append(f'<div style="display: flex; flex-direction: column; align-items: center;"><div class="trend-bar" style="height: {height}px; width: 20px;" title="{month["month"]}: ${month["amount"]:,.2f}"></div><div class="trend-label">{month["month"]}</div></div>')
        
        # Create the HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Public Donations Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #2E8B57 0%, #3CB371 25%, #20B2AA 50%, #48D1CC 75%, #40E0D0 100%);
                    min-height: 100vh;
                    color: #2c3e50;
                    padding: 15px;
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(15px);
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 15px 40px rgba(46, 139, 87, 0.25);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 25px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #3CB371;
                    position: relative;
                }}
                
                .header::before {{
                    content: '🌱';
                    position: absolute;
                    top: 0;
                    right: 25px;
                    font-size: 1.8rem;
                    opacity: 0.3;
                }}
                
                .header h1 {{
                    color: #2E8B57;
                    font-size: 2.2rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                }}
                
                .header p {{
                    color: #34495e;
                    font-size: 1rem;
                    font-weight: 500;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 25px;
                }}
                
                .stat-card {{
                    background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    transition: all 0.3s ease;
                    box-shadow: 0 8px 25px rgba(46, 139, 87, 0.25);
                    position: relative;
                    overflow: hidden;
                }}
                
                .stat-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #20B2AA, #48D1CC, #40E0D0);
                }}
                
                .stat-card:hover {{
                    transform: translateY(-5px) scale(1.02);
                    box-shadow: 0 12px 30px rgba(46, 139, 87, 0.35);
                }}
                
                .stat-number {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 10px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                }}
                
                .stat-label {{
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    opacity: 0.9;
                    font-weight: 500;
                }}
                
                .content-section {{
                    background: linear-gradient(135deg, rgba(46, 139, 87, 0.03) 0%, rgba(60, 179, 113, 0.03) 100%);
                    padding: 25px;
                    border-radius: 15px;
                    margin-bottom: 20px;
                    box-shadow: 0 5px 20px rgba(46, 139, 87, 0.1);
                    border: 1px solid rgba(46, 139, 87, 0.08);
                }}
                
                .section-title {{
                    font-size: 1.4rem;
                    margin-bottom: 20px;
                    color: #2E8B57;
                    border-bottom: 2px solid #3CB371;
                    padding-bottom: 10px;
                    font-weight: 600;
                    text-shadow: 1px 1px 1px rgba(0,0,0,0.05);
                }}
                
                .activity-item {{
                    background: rgba(255, 255, 255, 0.8);
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 10px;
                    border-left: 3px solid #2E8B57;
                    box-shadow: 0 2px 8px rgba(46, 139, 87, 0.08);
                    transition: all 0.2s ease;
                    font-size: 0.9rem;
                }}
                
                .activity-item:hover {{
                    transform: translateX(3px);
                    box-shadow: 0 4px 12px rgba(46, 139, 87, 0.15);
                }}
                
                .donor-item {{
                    background: rgba(255, 255, 255, 0.8);
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 2px 8px rgba(46, 139, 87, 0.08);
                    transition: all 0.2s ease;
                    font-size: 0.9rem;
                }}
                
                .donor-item:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(46, 139, 87, 0.15);
                }}
                
                .donor-rank {{
                    font-size: 1.5rem;
                    margin-right: 15px;
                }}
                
                .monthly-trend {{
                    display: flex;
                    align-items: end;
                    gap: 12px;
                    height: 80px;
                    margin-top: 15px;
                }}
                
                .trend-bar {{
                    background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                    border-radius: 6px 6px 0 0;
                    min-width: 20px;
                    position: relative;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 8px rgba(46, 139, 87, 0.2);
                }}
                
                .trend-bar:hover {{
                    transform: scaleY(1.1);
                    box-shadow: 0 4px 12px rgba(46, 139, 87, 0.3);
                }}
                
                .trend-label {{
                    font-size: 0.75rem;
                    color: #2E8B57;
                    text-align: center;
                    margin-top: 8px;
                    font-weight: 500;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 25px;
                    padding-top: 20px;
                    border-top: 2px solid #3CB371;
                    color: #2E8B57;
                    font-size: 0.85rem;
                    font-weight: 500;
                }}
                
                @media (max-width: 768px) {{
                    .container {{
                        padding: 20px;
                    }}
                    
                    .header h1 {{
                        font-size: 1.8rem;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Donations Dashboard</h1>
                    <p>Transparency in giving - Latest donation activities</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_donations:,}</div>
                        <div class="stat-label">Total Donations</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${total_amount:,.2f}</div>
                        <div class="stat-label">Total Amount</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{active_donors:,}</div>
                        <div class="stat-label">Active Donors</div>
                    </div>
                </div>
                
                <div class="content-section">
                    <h3 class="section-title">Recent Donations</h3>
                    {''.join([f'<div class="activity-item"><strong>{activity["message"]}</strong><br><small>Date: {activity["date"]}</small></div>' for activity in recent_activity])}
                </div>
                
                <div class="content-section">
                    <h3 class="section-title">Top Donors</h3>
                    {''.join([f'<div class="donor-item"><div><span class="donor-rank">{chr(127941 + i) if i < 3 else "🏅"}</span><strong>{donor["name"]}</strong></div><div>${donor["total"]:,.2f}</div></div>' for i, donor in enumerate(top_donors)])}
                </div>
                
                <div class="content-section">
                    <h3 class="section-title">Monthly Trend</h3>
                    <div class="monthly-trend">
                        {''.join(trend_bars)}
                    </div>
                </div>
                
                <div class="footer">
                    <p>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p>Data source: {latest_file}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Donations Dashboard</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #333;
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }}
                .error {{
                    text-align: center;
                    padding: 50px;
                    color: #666;
                }}
                .error h2 {{
                    color: #e74c3c;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Donations Dashboard</h1>
                    <p>Transparency in giving</p>
                </div>
                <div class="error">
                    <h2>Error Loading Data</h2>
                    <p>We're experiencing technical difficulties. Please try again later.</p>
                </div>
            </div>
        </body>
        </html>
        """)