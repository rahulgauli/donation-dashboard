from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse
from app.schema.admin_user import AdminUser
from app.security import verify_access_token
from typing import Optional


admin_router = APIRouter()

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Dependency to get the current authenticated user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = payload.get("sub")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return user

@admin_router.get("/admin", response_class=HTMLResponse)
async def admin_portal(request: Request):
    """
    Serve the admin dashboard HTML page.
    """
    # Always show the authentication check page first
    # The JavaScript will handle token validation and show the dashboard if authenticated
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .loading-container {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                flex-direction: column;
            }
            
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 5px solid #f3f3f3;
                border-top: 5px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-text {
                color: white;
                font-size: 1.2rem;
                text-align: center;
            }
            
            .auth-container {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 400px;
                display: none;
            }
            
            .auth-container h1 {
                color: #333;
                margin-bottom: 1rem;
            }
            
            .auth-container p {
                color: #666;
                margin-bottom: 2rem;
            }
            
            .login-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 1rem;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }
            
            .login-btn:hover {
                transform: translateY(-2px);
            }
            
            .dashboard-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                display: none;
            }
            
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                color: #333;
                font-size: 2rem;
                font-weight: 600;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .user-avatar {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 1.2rem;
            }
            
            .logout-btn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: background 0.3s ease;
            }
            
            .logout-btn:hover {
                background: #c0392b;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
                transition: transform 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-number {
                font-size: 2.5rem;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .stat-label {
                color: #666;
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .content-section {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            
            .section-title {
                font-size: 1.5rem;
                margin-bottom: 20px;
                color: #333;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 10px;
            }
            
            .action-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .action-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 500;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
            }
            
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            
            .action-btn.secondary {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }
            
            .action-btn.success {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            }
            
            .action-btn.warning {
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            }
            
            .welcome-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .welcome-message h2 {
                font-size: 1.8rem;
                margin-bottom: 10px;
            }
            
            .welcome-message p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            @media (max-width: 768px) {
                .dashboard-container {
                    padding: 10px;
                }
                
                .header {
                    flex-direction: column;
                    gap: 15px;
                    text-align: center;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <!-- Loading Screen -->
        <div class="loading-container" id="loadingContainer">
            <div class="loading-spinner"></div>
            <div class="loading-text">Checking authentication...</div>
        </div>
        
        <!-- Authentication Required -->
        <div class="auth-container" id="authContainer">
            <h1>Authentication Required</h1>
            <p>You need to be logged in to access the admin dashboard.</p>
            <a href="/" class="login-btn">Go to Login</a>
        </div>
        
        <!-- Dashboard -->
        <div class="dashboard-container" id="dashboardContainer">
            <div class="welcome-message">
                <h2>Welcome to the Admin Dashboard</h2>
                <p>Manage your donation system and monitor activities</p>
            </div>
            
            <div class="header">
                <h1>Admin Dashboard</h1>
                <div class="user-info">
                    <div class="user-avatar" id="userAvatar">A</div>
                    <span style="font-weight: 500;" id="userName">Admin</span>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">1,234</div>
                    <div class="stat-label">Total Donations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$45,678</div>
                    <div class="stat-label">Total Amount</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">567</div>
                    <div class="stat-label">Active Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">89</div>
                    <div class="stat-label">This Month</div>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Quick Actions</h3>
                <div class="action-buttons">
                    <button class="action-btn">View All Donations</button>
                    <button class="action-btn secondary">Manage Users</button>
                    <button class="action-btn success">Generate Reports</button>
                    <button class="action-btn warning">System Settings</button>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Recent Activity</h3>
                <div style="color: #666; line-height: 1.6;">
                    <p>• New donation received: $500 from John Doe</p>
                    <p>• User registration: jane.smith@example.com</p>
                    <p>• Monthly report generated successfully</p>
                    <p>• System backup completed</p>
                    <p>• New campaign created: "Summer Fundraiser"</p>
                </div>
            </div>
        </div>
        
        <script>
            // Check authentication on page load
            document.addEventListener('DOMContentLoaded', function() {
                const token = localStorage.getItem('authToken');
                
                if (!token) {
                    // No token, show login prompt
                    document.getElementById('loadingContainer').style.display = 'none';
                    document.getElementById('authContainer').style.display = 'block';
                    return;
                }
                
                // Token exists, validate it using the validation endpoint
                fetch('/auth/validate', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Token validation failed');
                    }
                })
                .then(data => {
                    // Token is valid, show dashboard
                    document.getElementById('loadingContainer').style.display = 'none';
                    document.getElementById('dashboardContainer').style.display = 'block';
                    
                    // Set user info
                    const user = data.user;
                    document.getElementById('userName').textContent = user;
                    document.getElementById('userAvatar').textContent = user[0].toUpperCase();
                    
                    // Add interactive features
                    const actionButtons = document.querySelectorAll('.action-btn');
                    actionButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            alert('This feature is coming soon!');
                        });
                    });
                    
                    // Add animation to stat cards
                    const statCards = document.querySelectorAll('.stat-card');
                    statCards.forEach((card, index) => {
                        setTimeout(() => {
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, index * 100);
                    });
                })
                .catch(error => {
                    console.error('Authentication error:', error);
                    // Token is invalid, clear it and show login
                    localStorage.removeItem('authToken');
                    document.getElementById('loadingContainer').style.display = 'none';
                    document.getElementById('authContainer').style.display = 'block';
                });
            });
            
            function logout() {
                // Clear any stored tokens
                localStorage.removeItem('authToken');
                sessionStorage.removeItem('authToken');
                
                // Redirect to login page
                window.location.href = '/';
            }
        </script>
    </body>
    </html>
    """)
