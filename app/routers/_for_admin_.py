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
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 25%, #20B2AA 50%, #48D1CC 75%, #40E0D0 100%);
                min-height: 100vh;
                color: #2c3e50;
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
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(46, 139, 87, 0.2);
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .header h1 {
                color: #2E8B57;
                font-size: 2.2rem;
                font-weight: 700;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .user-avatar {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 1.3rem;
                box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
                border: 3px solid rgba(255, 255, 255, 0.8);
            }
            
            .logout-btn {
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 0.9rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
            }
            
            .logout-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 25px;
                margin-bottom: 35px;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                text-align: center;
                transition: all 0.4s ease;
                box-shadow: 0 8px 32px rgba(46, 139, 87, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #2E8B57, #3CB371, #20B2AA, #48D1CC);
            }
            
            .stat-card::after {
                content: '🌿';
                position: absolute;
                top: 10px;
                right: 15px;
                font-size: 1.5rem;
                opacity: 0.2;
                animation: float 4s ease-in-out infinite;
            }
            
            .stat-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 15px 40px rgba(46, 139, 87, 0.25);
            }
            
            .stat-card:hover::after {
                animation: pulse 1s ease-in-out infinite;
            }
            
            .stat-number {
                font-size: 3rem;
                font-weight: 800;
                color: #2E8B57;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            
            .stat-label {
                color: #34495e;
                font-size: 1.1rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-weight: 600;
            }
            
            .content-section {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 35px;
                border-radius: 20px;
                margin-bottom: 25px;
                box-shadow: 0 8px 32px rgba(46, 139, 87, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .section-title {
                font-size: 1.8rem;
                margin-bottom: 25px;
                color: #2E8B57;
                border-bottom: 3px solid #3CB371;
                padding-bottom: 15px;
                font-weight: 700;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }
            
            .action-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-top: 25px;
            }
            
            .action-btn {
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                color: white;
                border: none;
                padding: 18px 25px;
                border-radius: 15px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 600;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
                box-shadow: 0 6px 20px rgba(46, 139, 87, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .action-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .action-btn:hover::before {
                left: 100%;
            }
            
            .action-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(46, 139, 87, 0.4);
            }
            
            .action-btn.secondary {
                background: linear-gradient(135deg, #20B2AA 0%, #48D1CC 100%);
            }
            
            .action-btn.success {
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            }
            
            .action-btn.warning {
                background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
            }
            
            .welcome-message {
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                color: white;
                padding: 30px;
                border-radius: 20px;
                margin-bottom: 25px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(46, 139, 87, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .welcome-message::before {
                content: '🌱';
                position: absolute;
                top: 10px;
                right: 20px;
                font-size: 2rem;
                opacity: 0.3;
            }
            
            .welcome-message h2 {
                font-size: 2rem;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            
            .welcome-message p {
                font-size: 1.2rem;
                opacity: 0.9;
                font-weight: 500;
            }
            
            /* Modal Styles */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgba(46, 139, 87, 0.8);
                backdrop-filter: blur(5px);
                padding-top: 60px;
            }

            .modal-content {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(15px);
                margin: 5% auto;
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                width: 80%;
                max-width: 600px;
                border-radius: 25px;
                box-shadow: 0 20px 60px rgba(46, 139, 87, 0.3);
                position: relative;
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 3px solid #3CB371;
            }

            .modal-header h2 {
                color: #2E8B57;
                font-size: 2rem;
                font-weight: 700;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }

            .close {
                color: #2E8B57;
                float: right;
                font-size: 32px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .close:hover,
            .close:focus {
                color: #3CB371;
                transform: scale(1.1);
            }

            .modal-body {
                padding: 25px;
            }

            .upload-area {
                border: 3px dashed #3CB371;
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: linear-gradient(135deg, rgba(46, 139, 87, 0.05) 0%, rgba(60, 179, 113, 0.05) 100%);
                margin-bottom: 25px;
                position: relative;
                overflow: hidden;
            }

            .upload-area::before {
                content: '🌿';
                position: absolute;
                top: 10px;
                right: 15px;
                font-size: 1.5rem;
                opacity: 0.3;
            }

            .upload-area:hover {
                border-color: #2E8B57;
                background: linear-gradient(135deg, rgba(46, 139, 87, 0.1) 0%, rgba(60, 179, 113, 0.1) 100%);
                transform: translateY(-2px);
            }

            .upload-icon {
                font-size: 4.5rem;
                color: #2E8B57;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }

            .upload-area p {
                color: #34495e;
                margin-bottom: 15px;
                font-weight: 500;
            }

            .upload-btn {
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 25px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 6px 20px rgba(46, 139, 87, 0.3);
            }

            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(46, 139, 87, 0.4);
            }

            .progress-bar {
                width: 100%;
                height: 12px;
                background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
                border-radius: 10px;
                margin-bottom: 15px;
                overflow: hidden;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
                border-radius: 10px;
                width: 0%;
                transition: width 0.3s ease;
                box-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
            }

            #uploadProgress p {
                color: #2E8B57;
                font-size: 1rem;
                text-align: center;
                font-weight: 600;
            }

            #uploadResult {
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
                text-align: center;
                font-weight: 600;
            }

            #uploadResult.success {
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                color: #155724;
                border: 2px solid #27ae60;
            }

            #uploadResult.error {
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                color: #721c24;
                border: 2px solid #e74c3c;
            }

            /* Uploads List Modal Styles */
            #uploadsList {
                padding: 25px;
                border-radius: 20px;
                background: linear-gradient(135deg, rgba(46, 139, 87, 0.05) 0%, rgba(60, 179, 113, 0.05) 100%);
                box-shadow: 0 8px 32px rgba(46, 139, 87, 0.15);
            }

            #uploadsList .loading-spinner {
                margin: 0 auto 25px auto;
            }

            #uploadsList p {
                color: #2E8B57;
                text-align: center;
                padding: 15px;
                font-weight: 600;
            }
            
            .monthly-trend {
                display: flex;
                align-items: end;
                gap: 10px;
                height: 100px;
                margin-top: 15px;
            }
            
            .trend-bar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 3px 3px 0 0;
                min-width: 20px;
                position: relative;
                transition: all 0.3s ease;
            }
            
            .trend-bar:hover {
                transform: scaleY(1.1);
            }
            
            .trend-label {
                font-size: 0.8rem;
                color: #666;
                text-align: center;
                margin-top: 5px;
            }
            
            .loading-pulse {
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
            
            @keyframes shimmer {
                0% { background-position: -200px 0; }
                100% { background-position: calc(200px + 100%) 0; }
            }
            
            .floating-leaf {
                position: fixed;
                font-size: 2rem;
                opacity: 0.1;
                animation: float 6s ease-in-out infinite;
                pointer-events: none;
                z-index: -1;
            }
            
            .floating-leaf:nth-child(1) { top: 10%; left: 5%; animation-delay: 0s; }
            .floating-leaf:nth-child(2) { top: 20%; right: 10%; animation-delay: 2s; }
            .floating-leaf:nth-child(3) { bottom: 30%; left: 15%; animation-delay: 4s; }
            .floating-leaf:nth-child(4) { bottom: 20%; right: 5%; animation-delay: 1s; }
            
            .data-source {
                font-size: 0.8rem;
                color: #999;
                text-align: center;
                margin-top: 10px;
                font-style: italic;
            }
            
            .refresh-btn {
                background: #28a745;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8rem;
                margin-left: 10px;
            }
            
            .refresh-btn:hover {
                background: #218838;
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
        <!-- Floating Nature Elements -->
        <div class="floating-leaf">🍃</div>
        <div class="floating-leaf">🌿</div>
        <div class="floating-leaf">🌱</div>
        <div class="floating-leaf">🍀</div>
        
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
                    <a href="/public-dashboard" target="_blank" style="
                        background: #28a745;
                        color: white;
                        text-decoration: none;
                        padding: 8px 16px;
                        border-radius: 5px;
                        font-size: 0.9rem;
                        margin-right: 10px;
                    ">🌐 Public View</a>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="totalDonations">-</div>
                    <div class="stat-label">Total Donations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalAmount">-</div>
                    <div class="stat-label">Total Amount</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="activeDonors">-</div>
                    <div class="stat-label">Active Donors</div>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Quick Actions</h3>
                <div class="action-buttons">
                    <button class="action-btn" onclick="openUploadModal()">Upload Excel File</button>
                    <button class="action-btn secondary" onclick="viewUploads()">View Uploads</button>
                    <button class="action-btn success" onclick="downloadTemplate()">Download Template</button>
                    <button class="action-btn warning" onclick="refreshDashboard()">Refresh Data</button>
                </div>
            </div>
            
            <!-- File Upload Modal -->
            <div id="uploadModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Upload Excel File</h2>
                        <span class="close" onclick="closeUploadModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div style="margin-bottom: 20px; text-align: center;">
                            <p style="color: #666; margin-bottom: 10px;">Need a template? Download our sample Excel file:</p>
                            <button onclick="downloadTemplate()" style="
                                background: #28a745;
                                color: white;
                                border: none;
                                padding: 8px 16px;
                                border-radius: 5px;
                                cursor: pointer;
                                font-size: 0.9rem;
                            ">📥 Download Template</button>
                        </div>
                        <div class="upload-area" id="uploadArea">
                            <div class="upload-icon">📁</div>
                            <p>Drag and drop your Excel file here</p>
                            <p>or</p>
                            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">
                            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">Choose File</button>
                        </div>
                        <div id="uploadProgress" style="display: none;">
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                            <p id="uploadStatus">Uploading...</p>
                        </div>
                        <div id="uploadResult" style="display: none;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Uploads List Modal -->
            <div id="uploadsModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Uploaded Files</h2>
                        <span class="close" onclick="closeUploadsModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div id="uploadsList">
                            <div class="loading-spinner"></div>
                            <p>Loading files...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Recent Activity</h3>
                <div id="recentActivity" style="color: #666; line-height: 1.6;">
                    <p>Loading recent activity...</p>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Top Donors</h3>
                <div id="topDonors" style="color: #666; line-height: 1.6;">
                    <p>Loading top donors...</p>
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">Monthly Trend</h3>
                <div id="monthlyTrend" style="color: #666; line-height: 1.6;">
                    <p>Loading monthly trend...</p>
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
                    
                    // Load dashboard data
                    loadDashboardData();
                })
                .catch(error => {
                    console.error('Authentication error:', error);
                    // Token is invalid, clear it and show login
                    localStorage.removeItem('authToken');
                    document.getElementById('loadingContainer').style.display = 'none';
                    document.getElementById('authContainer').style.display = 'block';
                });
            });
            
            // Dashboard Data Functions
            function loadDashboardData() {
                const token = localStorage.getItem('authToken');
                
                fetch('/dashboard-data', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    updateDashboardStats(data);
                    updateRecentActivity(data.recent_activity);
                    updateTopDonors(data.top_donors);
                    updateMonthlyTrend(data.monthly_trend);
                })
                .catch(error => {
                    console.error('Error loading dashboard data:', error);
                    showDashboardError();
                });
            }
            
            function updateDashboardStats(data) {
                document.getElementById('totalDonations').textContent = data.total_donations.toLocaleString();
                document.getElementById('totalAmount').textContent = `$${data.total_amount.toLocaleString()}`;
                document.getElementById('activeDonors').textContent = data.active_donors.toLocaleString();
            }
            
            function updateRecentActivity(activities) {
                const container = document.getElementById('recentActivity');
                if (activities.length === 0) {
                    container.innerHTML = '<p>No recent activity found.</p>';
                    return;
                }
                
                let html = '';
                activities.forEach(activity => {
                    html += `<p>• ${activity.message} (${activity.date})</p>`;
                });
                container.innerHTML = html;
            }
            
            function updateTopDonors(donors) {
                const container = document.getElementById('topDonors');
                if (donors.length === 0) {
                    container.innerHTML = '<p>No donor data available.</p>';
                    return;
                }
                
                let html = '';
                donors.forEach((donor, index) => {
                    const rank = index + 1;
                    const emoji = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '🏅';
                    html += `<p>${emoji} ${donor.name}: $${donor.total.toLocaleString()}</p>`;
                });
                container.innerHTML = html;
            }
            
            function updateMonthlyTrend(trend) {
                const container = document.getElementById('monthlyTrend');
                if (trend.length === 0) {
                    container.innerHTML = '<p>No trend data available.</p>';
                    return;
                }
                
                // Find the maximum amount for scaling
                const maxAmount = Math.max(...trend.map(month => month.amount));
                
                let html = '<div class="monthly-trend">';
                trend.forEach(month => {
                    const height = maxAmount > 0 ? (month.amount / maxAmount) * 80 : 0;
                    html += `
                        <div style="display: flex; flex-direction: column; align-items: center;">
                            <div class="trend-bar" style="height: ${height}px; width: 30px;" title="${month.month}: $${month.amount.toLocaleString()}"></div>
                            <div class="trend-label">${month.month}</div>
                        </div>
                    `;
                });
                html += '</div>';
                container.innerHTML = html;
            }
            
            function showDashboardError() {
                document.getElementById('totalDonations').textContent = 'Error';
                document.getElementById('totalAmount').textContent = 'Error';
                document.getElementById('activeDonors').textContent = 'Error';
                document.getElementById('recentActivity').innerHTML = '<p>Error loading data. Please try refreshing.</p>';
                document.getElementById('topDonors').innerHTML = '<p>Error loading data. Please try refreshing.</p>';
                document.getElementById('monthlyTrend').innerHTML = '<p>Error loading data. Please try refreshing.</p>';
            }
            
            function refreshDashboard() {
                loadDashboardData();
                // Show a brief loading state
                document.getElementById('totalDonations').textContent = '...';
                document.getElementById('totalAmount').textContent = '...';
                document.getElementById('activeDonors').textContent = '...';
                document.getElementById('recentActivity').innerHTML = '<p>Refreshing...</p>';
                document.getElementById('topDonors').innerHTML = '<p>Refreshing...</p>';
                document.getElementById('monthlyTrend').innerHTML = '<p>Refreshing...</p>';
            }
            
            function logout() {
                // Clear any stored tokens
                localStorage.removeItem('authToken');
                sessionStorage.removeItem('authToken');
                
                // Redirect to login page
                window.location.href = '/';
            }

            // Modal Functions
            function openUploadModal() {
                document.getElementById('uploadModal').style.display = 'block';
                setupFileUpload();
            }

            function closeUploadModal() {
                document.getElementById('uploadModal').style.display = 'none';
                resetUploadForm();
            }

            function openUploadsModal() {
                document.getElementById('uploadsModal').style.display = 'block';
                loadUploads();
            }

            function closeUploadsModal() {
                document.getElementById('uploadsModal').style.display = 'none';
            }

            function viewUploads() {
                openUploadsModal();
            }

            // File Upload Functions
            function setupFileUpload() {
                const uploadArea = document.getElementById('uploadArea');
                const fileInput = document.getElementById('fileInput');

                // Drag and drop functionality
                uploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadArea.style.borderColor = '#667eea';
                    uploadArea.style.backgroundColor = '#f0f4ff';
                });

                uploadArea.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    uploadArea.style.borderColor = '#ccc';
                    uploadArea.style.backgroundColor = '#f9f9f9';
                });

                uploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadArea.style.borderColor = '#ccc';
                    uploadArea.style.backgroundColor = '#f9f9f9';
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        handleFileUpload(files[0]);
                    }
                });

                // File input change
                fileInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        handleFileUpload(e.target.files[0]);
                    }
                });
            }

            function handleFileUpload(file) {
                // Validate file type
                const fileName = file.name.toLowerCase();
                if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
                    showUploadResult('Please select a valid Excel file (.xlsx or .xls)', 'error');
                    return;
                }

                // Show progress
                document.getElementById('uploadArea').style.display = 'none';
                document.getElementById('uploadProgress').style.display = 'block';
                document.getElementById('uploadResult').style.display = 'none';

                // Simulate progress
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += 10;
                    document.getElementById('progressFill').style.width = progress + '%';
                    if (progress >= 100) {
                        clearInterval(progressInterval);
                        uploadFile(file);
                    }
                }, 200);
            }

            function uploadFile(file) {
                const token = localStorage.getItem('authToken');
                const formData = new FormData();
                formData.append('file', file);

                fetch('/upload-excel', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        showUploadResult(`✅ ${data.message}<br>📁 File: ${data.filename}<br>📊 Records: ${data.records_count}`, 'success');
                        
                        // Refresh dashboard data after successful upload
                        setTimeout(() => {
                            if (typeof loadDashboardData === 'function') {
                                loadDashboardData();
                            }
                        }, 1000);
                    } else {
                        showUploadResult('❌ Upload failed: ' + (data.detail || 'Unknown error'), 'error');
                    }
                })
                .catch(error => {
                    console.error('Upload error:', error);
                    showUploadResult('❌ Upload failed: Network error', 'error');
                })
                .finally(() => {
                    document.getElementById('uploadProgress').style.display = 'none';
                });
            }

            function showUploadResult(message, type) {
                const resultDiv = document.getElementById('uploadResult');
                resultDiv.innerHTML = message;
                resultDiv.className = type;
                resultDiv.style.display = 'block';
            }

            function resetUploadForm() {
                document.getElementById('uploadArea').style.display = 'block';
                document.getElementById('uploadProgress').style.display = 'none';
                document.getElementById('uploadResult').style.display = 'none';
                document.getElementById('fileInput').value = '';
                document.getElementById('progressFill').style.width = '0%';
            }

            // Load Uploads Function
            function loadUploads() {
                const uploadsList = document.getElementById('uploadsList');
                uploadsList.innerHTML = '<div class="loading-spinner"></div><p>Loading files...</p>';

                const token = localStorage.getItem('authToken');

                fetch('/list-uploads', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.files && data.files.length > 0) {
                        displayUploads(data.files);
                    } else {
                        uploadsList.innerHTML = '<p>No files uploaded yet.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading uploads:', error);
                    uploadsList.innerHTML = '<p>Error loading files. Please try again.</p>';
                });
            }

            function displayUploads(files) {
                const uploadsList = document.getElementById('uploadsList');
                let html = '<div style="max-height: 400px; overflow-y: auto;">';
                
                files.forEach(file => {
                    const fileSize = formatFileSize(file.size);
                    const createdDate = new Date(file.created).toLocaleString();
                    
                    html += `
                        <div style="
                            background: white;
                            padding: 15px;
                            margin-bottom: 10px;
                            border-radius: 8px;
                            border-left: 4px solid #667eea;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h4 style="margin: 0 0 5px 0; color: #333;">${file.filename}</h4>
                                    <p style="margin: 0; color: #666; font-size: 0.9rem;">
                                        📅 Created: ${createdDate}<br>
                                        📏 Size: ${fileSize}
                                    </p>
                                </div>
                                <div style="text-align: right;">
                                    <button onclick="viewFile('${file.filename}')" style="
                                        background: #667eea;
                                        color: white;
                                        border: none;
                                        padding: 5px 10px;
                                        border-radius: 4px;
                                        cursor: pointer;
                                        font-size: 0.8rem;
                                    ">View</button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
                uploadsList.innerHTML = html;
            }

            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }

            function viewFile(filename) {
                alert(`Viewing file: ${filename}\n\nThis would open the file viewer in a real application.`);
            }

            function downloadTemplate() {
                const token = localStorage.getItem('authToken');
                const url = `/download-template?token=${token}`;
                window.location.href = url;
            }
        </script>
    </body>
    </html>
    """)
