# Donation Dashboard

Welcome! This dashboard lets you securely manage and view donation data. You can upload Excel files, see donation stats, and access a public dashboard for transparency.

---

## How to Run the App

### 1. Prerequisites

- **Docker**:  
  Make sure Docker is installed on your computer.
  - [Download Docker for Mac](https://www.docker.com/products/docker-desktop/)
  - [Download Docker for Windows](https://www.docker.com/products/docker-desktop/)

---

### 2. Start the App

#### **For Mac Users**

1. **Open Terminal**  
   Find and open the Terminal app.

2. **Go to the Project Folder**  
   Type:
   ```
   cd /Users/raulgauli/donation-dashboard
   ```

3. **Start the Dashboard**  
   Type:
   ```
   docker-compose up
   ```

#### **For Windows Users**

1. **Open Command Prompt or PowerShell**  
   Press `Win + R`, type `cmd` or `powershell`, and press Enter.

2. **Go to the Project Folder**  
   Type:
   ```
   cd C:\Users\<your-username>\donation-dashboard
   ```
   *(Replace `<your-username>` with your Windows username)*

3. **Start the Dashboard**  
   Type:
   ```
   docker-compose up
   ```

---

### 3. Access the Dashboard

- **Login Page:**  
  Open your web browser and go to [http://localhost:8000](http://localhost:8000)
- **Public Dashboard:**  
  Anyone can view [http://localhost:8000/public-dashboard](http://localhost:8000/public-dashboard)

---

### 4. Login

- Use your provided username and password (see `app/admin_info/login.json`).
- After logging in, you’ll see the admin portal.

---

### 5. Features

- **Upload Excel:**  
  Upload donation data in Excel format.
- **Download Template:**  
  Download a sample Excel template.
- **View Dashboard:**  
  See donation stats, top donors, and trends.
- **Public Dashboard:**  
  Share donation stats with anyone.

---

### 6. Stopping the App

- In Terminal or Command Prompt, press `Ctrl + C` to stop.
- To remove containers, type:
  ```
  docker-compose down
  ```

---

## Need Help?

If you have any issues, ask your admin or contact support.

---