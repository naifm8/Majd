# 🌟 Majd – Academy Management Platform

Majd is a unified platform for academies to showcase their programs with fees and allow parents to easily register their children.  
The system provides separate dashboards for **Academy Admins**, **Trainers**, and **Parents** with full role-based features.

---

## 🎯 Target Audience
- **Parents** → Manage children’s profiles and register them in academy sessions.  
- **Academy Admins** → Manage academy programs, trainers, and students.  
- **Trainers** → Manage classes, evaluations, and apply to join academies.  

---

## 🚀 Features

### 🏫 Academy Dashboard
- Full **CRUD** for programs and sessions.  
- Manage trainers and students within the academy.  
- Review and **approve/reject trainer applications**.  
- Access detailed reports and statistics.  

### 👨‍🏫 Trainer Dashboard
- View schedule and upcoming classes.  
- Track students and their progress.  
- Add **attendance** and **evaluations**.  
- Apply to join academies.  

### 👨‍👩‍👧 Parent Dashboard
- Add and update child profiles.  
- Register children in academy sessions.  
- Track attendance and performance.  

### 📊 Reports & Analytics
- Multiple reports and statistics for academies, trainers, and parents.  

---

## 🛠️ Tech Stack
- **Backend**: Python, Django  
- **Frontend**: Django Templates (Bootstrap for styling)  
- **Database**: PostgreSQL  
- **Storage**: Cloud-based (media files and images stored in the cloud)  
- **Environment**: `.env` file required for sensitive keys (DB, Cloudinary, etc.)  

---
## 💳 Subscriptions

### 🏫 Academy Subscriptions
- Each academy can subscribe to the platform to showcase its programs.  
- Subscriptions unlock features such as:
  - Managing trainers and students within the academy.  
  - Accessing advanced reports and analytics.  
- Subscription fees are applied at the academy level.

### 👨‍👩‍👧 Student Subscriptions
- Parents can register their children in specific academy sessions.  
- Subscription per student includes:
  - Enrollment in academy programs and classes.  
  - Attendance tracking.  
  - Progress and evaluation reports.  
- Fees are determined by the academy program and paid per child.

## ⚙️ Installation & Setup

Clone the repository:
```bash
git clone <repo-url>
cd majd
```

Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run migrations and load initial fixtures:
```bash
python manage.py migrate
python manage.py loaddata groups.json>
```

Start the development server:
```bash
python manage.py runserver
```

Access the app at 👉 `http://127.0.0.1:8000/`




## 🔮 Future Work
- Advanced analytics for student performance.  
- Multi-language support (English/Arabic).  
