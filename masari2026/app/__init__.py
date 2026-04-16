from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
import sqlite3
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'accounts.login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'warning'


def _migrate_db(app):
    """إضافة الأعمدة الجديدة تلقائياً إن لم تكن موجودة."""
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not uri.startswith('sqlite'):
        return

    # استخراج المسار الصحيح: sqlite:/// → مسار نسبي لمجلد instance
    raw = uri.replace('sqlite:///', '')
    if os.path.isabs(raw):
        db_path = raw
    else:
        db_path = os.path.join(app.instance_path, raw)

    # إنشاء مجلد instance إن لم يكن موجوداً
    os.makedirs(app.instance_path, exist_ok=True)

    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrations = {
        'users': ['phone'],
        'opportunities': [
            'responsibilities', 'benefits', 'required_skills',
            'required_certifications', 'work_type', 'location',
            'salary_range', 'gender_preference', 'deadline'
        ],
        'applications': [
            'contact_email', 'contact_phone', 'applicant_education',
            'applicant_experience', 'applicant_skills', 'current_position',
            'motivation', 'relevant_experience', 'availability',
            'compatibility_score'
        ],
    }

    for table, columns in migrations.items():
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cursor.fetchall()}
        except Exception:
            continue
        for col in columns:
            if col not in existing:
                col_type = 'INTEGER DEFAULT 0' if col == 'compatibility_score' else 'TEXT'
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

    conn.commit()
    conn.close()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.accounts.routes import accounts
    from app.opportunities.routes import opportunities

    app.register_blueprint(accounts)
    app.register_blueprint(opportunities)

    # Context processor لإتاحة السنة الحالية في جميع القوالب
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    with app.app_context():
        _migrate_db(app)
        db.create_all()

    return app
