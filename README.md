# 🚀 AI-First Laundry Order Management System

A lightweight, production-inspired backend system built using **Flask + AI-assisted development**, designed to simulate real-world order processing workflows.

> ⚡ Built within 72 hours using AI tools (ChatGPT, Copilot) with a focus on **clean code, fast execution, and practical problem-solving**

---

## ✨ Highlights

- 🧠 AI-assisted development (prompt-driven coding)
- ⚙️ Clean backend architecture (modular Flask design)
- 📊 Smart dashboard with real-time business insights
- 🔍 Advanced filtering (status, customer name, phone)
- 📅 Estimated delivery date logic
- 🧪 Property-based testing using Hypothesis
- 🌐 Minimal frontend (HTML + JS, no frameworks)

---

## 🎯 Why This Project?

This project simulates a real-world laundry business workflow:

- Order intake → processing → delivery  
- Revenue tracking and analytics  
- Customer-based filtering and search  

It demonstrates:
- Backend API design
- Business logic implementation
- AI-assisted development workflow
- Testing using property-based techniques

---

## 🏗️ Project Structure


project/
│
├── app.py # Flask routes & request handling
├── constants.py # Prices, statuses, transitions
├── helpers.py # Business logic
├── validators.py # Input validation
├── requirements.txt # Dependencies
│
├── static/
│ └── index.html # Simple frontend
│
└── tests/
├── conftest.py
├── test_create_order.py
├── test_update_status.py
├── test_get_orders.py
├── test_dashboard.py
└── test_response_format.py


---

## ⚙️ Features Implemented

### ✅ Order Management
- Create orders with garments and quantity
- Automatic bill calculation
- Unique Order ID generation
- Estimated delivery date (current date + 2 days)

### 🔄 Order Status Tracking
- Lifecycle:

RECEIVED → PROCESSING → READY → DELIVERED

- Strict transition validation

### 🔍 Filtering
- Filter by:
- Status
- Customer name (partial match)
- Phone number

### 📊 Dashboard
- Total orders
- Total revenue
- Average order value
- Orders per status
- Most common garment

---

## 📡 API Overview

### `POST /orders`
Create a new order

### `PUT /orders/<order_id>/status`
Update order status

### `GET /orders`
Fetch all orders (with filters)

### `GET /dashboard`
Get aggregated business metrics

---

## 📊 Data Model

Each order contains:

- `order_id` (UUID)
- `customer_name`
- `phone`
- `garments`
- `status`
- `total_bill`
- `estimated_delivery_date`

---

## ⚙️ Getting Started

### 1. Clone the repository

git clone Laundry-Order-Management-System

cd Laundry-Order-Management-System


### 2. Setup environment

python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # Mac/Linux


### 3. Install dependencies

pip install -r requirements.txt


### 4. Run the server

python app.py


👉 Open: http://localhost:5000

---

## 🧪 Running Tests


pytest tests/ -v


✔ Includes property-based testing using Hypothesis  
✔ Covers edge cases and validation scenarios  

---

## 🤖 AI Usage Report

### Tools Used
- ChatGPT
- GitHub Copilot

### How AI Was Used
- Generated initial API structure
- Helped design endpoints and workflows
- Assisted in writing validation and test cases
- Suggested improvements for dashboard and filtering

### Sample Prompts
- “Create a Flask API for order management with dashboard”
- “Add filtering logic for status, name, phone”
- “Refactor code for better readability and modularity”

### Where AI Fell Short
- Did not handle edge cases properly
- Generated repetitive logic
- Weak validation in initial output

### Improvements Made
- Added structured validation layer
- Refactored into helper modules
- Implemented strict business rules
- Cleaned and optimized code

> 💡 Insight: AI accelerated development significantly, but human intervention was required to ensure correctness, structure, and maintainability.

---

## ⚖️ Tradeoffs

- Used in-memory storage (no database) for simplicity and speed
- Minimal frontend (focused on backend functionality)
- No authentication (kept scope limited)

---

## 🚀 Future Improvements

- Add database (MongoDB / PostgreSQL)
- Implement authentication system
- Build advanced frontend (React)
- Add real-time notifications
- Deploy with CI/CD pipeline

---

## 🌐 Deployment

You can deploy using:
- Render
- Railway
- Docker
- PythonAnywhere

---

# 🧠 Final Note

This project focuses on:
- Practical backend engineering  
- Smart use of AI tools  
- Clean, maintainable code  

> Built with an **AI-first mindset**, balancing speed, quality, and real-world applicability.
