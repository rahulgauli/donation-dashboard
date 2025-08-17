from fastapi import FastAPI, HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from app.routers._for_admin_ import admin_router

from app.middleware_token import BearerAuthASGIMiddleware
from app.security import creds, create_access_token
from typing import Optional
from fastapi import Header
from app.security import verify_access_token


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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .login-container {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
            }
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .login-header h1 {
                color: #333;
                margin: 0;
                font-size: 2rem;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #555;
                font-weight: 500;
            }
            .form-group input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e1e5e9;
                border-radius: 5px;
                font-size: 1rem;
                box-sizing: border-box;
                transition: border-color 0.3s ease;
            }
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
            }
            .login-btn {
                width: 100%;
                padding: 0.75rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            .login-btn:hover {
                transform: translateY(-2px);
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
            }
            .success-message {
                color: #27ae60;
                text-align: center;
                margin-top: 1rem;
                display: none;
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
        </div>

        <script>
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