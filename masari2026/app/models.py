from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    education_level = db.Column(db.String(50), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    opportunities = db.relationship('Opportunity', backref='author', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='applicant', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skills = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    experience_desc = db.Column(db.Text, nullable=True)
    cv_link = db.Column(db.String(300), nullable=True)

    def __repr__(self):
        return f"Profile(user_id={self.user_id})"


class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    # متطلبات الفرصة
    min_education = db.Column(db.String(50), nullable=True)
    min_experience = db.Column(db.String(50), nullable=True)
    required_skills = db.Column(db.Text, nullable=True)
    required_certifications = db.Column(db.Text, nullable=True)
    # تفاصيل إضافية
    work_type = db.Column(db.String(30), nullable=True)  # حضوري / عن بعد / هجين
    location = db.Column(db.String(100), nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)
    gender_preference = db.Column(db.String(20), nullable=True)  # ذكور / إناث / الجميع
    deadline = db.Column(db.DateTime, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    applications = db.relationship('Application', backref='opportunity', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Opportunity('{self.title}', '{self.company}')"


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False)
    # معلومات التواصل
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    # مؤهلات المتقدم
    applicant_education = db.Column(db.String(50), nullable=True)
    applicant_experience = db.Column(db.String(50), nullable=True)
    applicant_skills = db.Column(db.Text, nullable=True)
    current_position = db.Column(db.String(100), nullable=True)
    # أسئلة الاستبيان
    motivation = db.Column(db.Text, nullable=True)
    relevant_experience = db.Column(db.Text, nullable=True)
    availability = db.Column(db.String(50), nullable=True)
    # النتائج
    compatibility_score = db.Column(db.Integer, default=0)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f"Application(user={self.user_id}, opp={self.opportunity_id})"


# حساب نسبة التوافق
EDU_LEVELS = {'ثانوي': 1, 'دبلوم': 2, 'بكالوريوس': 3, 'ماجستير': 4, 'دكتوراه': 5}
EXP_LEVELS = {'بدون خبرة': 0, 'سنة أو أقل': 1, '1-3 سنوات': 2, '3-5 سنوات': 3, '+5 سنوات': 4}


def calculate_compatibility(opp, application):
    score = 0
    total = 0

    # التعليم
    if opp.min_education:
        total += 30
        req = EDU_LEVELS.get(opp.min_education, 0)
        app = EDU_LEVELS.get(application.applicant_education, 0)
        if app >= req:
            score += 30
        elif app == req - 1:
            score += 15

    # الخبرة
    if opp.min_experience:
        total += 30
        req = EXP_LEVELS.get(opp.min_experience, 0)
        app = EXP_LEVELS.get(application.applicant_experience, 0)
        if app >= req:
            score += 30
        elif app == req - 1:
            score += 15

    # المهارات
    if opp.required_skills:
        total += 40
        req_skills = {s.strip().lower() for s in opp.required_skills.split(',') if s.strip()}
        app_skills = {s.strip().lower() for s in (application.applicant_skills or '').split(',') if s.strip()}
        if req_skills:
            overlap = len(req_skills & app_skills)
            score += int(40 * overlap / len(req_skills))

    if total == 0:
        return 100
    return int(score / total * 100)
