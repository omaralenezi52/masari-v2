from flask import Blueprint, render_template, url_for, flash, redirect, request
from app import db
from app.accounts.forms import RegistrationForm, LoginForm, ProfileForm
from app.models import User, Profile
from flask_login import login_user, current_user, logout_user, login_required
import hashlib

accounts = Blueprint('accounts', __name__)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@accounts.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('opportunities.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # التحقق من عدم تكرار البريد الإلكتروني أو اسم المستخدم
        if User.query.filter_by(email=form.email.data).first():
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return render_template('register.html', title='تسجيل جديد', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash('اسم المستخدم مستخدم بالفعل', 'danger')
            return render_template('register.html', title='تسجيل جديد', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hash_password(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء حسابك بنجاح! أكمل بياناتك الآن.', 'success')
        return redirect(url_for('accounts.login'))
    return render_template('register.html', title='تسجيل جديد', form=form)


@accounts.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('opportunities.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == hash_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not user.education_level:
                return redirect(url_for('accounts.onboarding'))
            return redirect(next_page or url_for('opportunities.home'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    return render_template('login.html', title='تسجيل الدخول', form=form)


@accounts.route("/onboarding", methods=['GET', 'POST'])
@login_required
def onboarding():
    if request.method == 'POST':
        edu_level = request.form.get('edu_level')
        if not edu_level:
            flash('يرجى اختيار المستوى التعليمي', 'warning')
            return render_template('onboarding.html', title='أكمل بياناتك')

        current_user.education_level = edu_level

        # إنشاء ملف شخصي إن لم يكن موجوداً
        if not current_user.profile:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)

        db.session.commit()
        flash('أهلاً بك في مساري 2026! يمكنك الآن تصفح الفرص.', 'success')
        return redirect(url_for('opportunities.home'))
    return render_template('onboarding.html', title='أكمل بياناتك')


@accounts.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    user_profile = Profile.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        if not user_profile:
            user_profile = Profile(user_id=current_user.id)
            db.session.add(user_profile)

        user_profile.skills = form.skills.data
        user_profile.experience_years = form.experience_years.data
        user_profile.experience_desc = form.experience_desc.data
        user_profile.cv_link = form.cv_link.data
        db.session.commit()
        flash('تم تحديث ملفك الشخصي بنجاح!', 'success')
        return redirect(url_for('accounts.profile'))

    elif request.method == 'GET' and user_profile:
        form.skills.data = user_profile.skills
        form.experience_years.data = user_profile.experience_years
        form.experience_desc.data = user_profile.experience_desc
        form.cv_link.data = user_profile.cv_link

    return render_template('profile.html', title='ملفي الشخصي', form=form, profile=user_profile)


@accounts.route("/logout")
@login_required
def logout():
    logout_user()
    flash('تم تسجيل خروجك بنجاح', 'info')
    return redirect(url_for('opportunities.home'))
