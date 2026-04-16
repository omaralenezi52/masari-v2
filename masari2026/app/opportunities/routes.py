from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from app import db
from app.opportunities.forms import OpportunityForm
from app.models import Opportunity, Application, User, calculate_compatibility
from flask_login import current_user, login_required
from sqlalchemy import func
from datetime import datetime

opportunities = Blueprint('opportunities', __name__)


@opportunities.route("/")
@opportunities.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    opp_type = request.args.get('type', '')
    search = request.args.get('q', '')

    query = Opportunity.query

    if opp_type:
        query = query.filter_by(type=opp_type)
    if search:
        query = query.filter(
            Opportunity.title.ilike(f'%{search}%') |
            Opportunity.company.ilike(f'%{search}%') |
            Opportunity.description.ilike(f'%{search}%')
        )

    opps = query.order_by(Opportunity.date_posted.desc()).paginate(page=page, per_page=9, error_out=False)

    # إحصائيات حقيقية
    total_users = User.query.count()
    total_opps  = Opportunity.query.count()
    total_apps  = Application.query.count()

    return render_template(
        'home.html',
        opportunities=opps,
        opp_type=opp_type,
        search=search,
        total_users=total_users,
        total_opps=total_opps,
        total_apps=total_apps,
    )


@opportunities.route("/opportunity/<int:opp_id>")
def opportunity_detail(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    already_applied = False
    is_owner = False
    if current_user.is_authenticated:
        is_owner = (current_user.id == opp.user_id)
        already_applied = Application.query.filter_by(
            user_id=current_user.id,
            opportunity_id=opp_id
        ).first() is not None
    return render_template('opportunity_detail.html', opp=opp,
                           already_applied=already_applied, is_owner=is_owner)


@opportunities.route("/opportunity/new", methods=['GET', 'POST'])
@login_required
def new_opportunity():
    form = OpportunityForm()
    if form.validate_on_submit():
        deadline = None
        deadline_str = request.form.get('deadline', '')
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                pass

        opp = Opportunity(
            title=form.title.data,
            description=form.description.data,
            type=form.type.data,
            company=form.company.data,
            work_type=form.work_type.data or None,
            location=form.location.data or None,
            salary_range=form.salary_range.data or None,
            gender_preference=form.gender_preference.data or 'الجميع',
            min_education=form.min_education.data or None,
            min_experience=form.min_experience.data or None,
            required_skills=form.required_skills.data or None,
            required_certifications=form.required_certifications.data or None,
            responsibilities=form.responsibilities.data or None,
            benefits=form.benefits.data or None,
            deadline=deadline,
            user_id=current_user.id
        )
        db.session.add(opp)
        db.session.commit()
        flash('تم نشر الفرصة بنجاح!', 'success')
        return redirect(url_for('opportunities.home'))
    return render_template('create_opp.html', title='نشر فرصة جديدة', form=form)


@opportunities.route("/opportunity/<int:opp_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    form = OpportunityForm()
    if form.validate_on_submit():
        opp.title = form.title.data
        opp.description = form.description.data
        opp.type = form.type.data
        opp.company = form.company.data
        opp.work_type = form.work_type.data or None
        opp.location = form.location.data or None
        opp.salary_range = form.salary_range.data or None
        opp.gender_preference = form.gender_preference.data or 'الجميع'
        opp.min_education = form.min_education.data or None
        opp.min_experience = form.min_experience.data or None
        opp.required_skills = form.required_skills.data or None
        opp.required_certifications = form.required_certifications.data or None
        opp.responsibilities = form.responsibilities.data or None
        opp.benefits = form.benefits.data or None
        deadline_str = request.form.get('deadline', '')
        if deadline_str:
            try:
                opp.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                pass
        else:
            opp.deadline = None
        db.session.commit()
        flash('تم تحديث الفرصة بنجاح!', 'success')
        return redirect(url_for('opportunities.opportunity_detail', opp_id=opp.id))
    elif request.method == 'GET':
        form.title.data = opp.title
        form.company.data = opp.company
        form.type.data = opp.type
        form.description.data = opp.description
        form.work_type.data = opp.work_type or ''
        form.location.data = opp.location or ''
        form.salary_range.data = opp.salary_range or ''
        form.gender_preference.data = opp.gender_preference or 'الجميع'
        form.min_education.data = opp.min_education or ''
        form.min_experience.data = opp.min_experience or ''
        form.required_skills.data = opp.required_skills or ''
        form.required_certifications.data = opp.required_certifications or ''
        form.responsibilities.data = opp.responsibilities or ''
        form.benefits.data = opp.benefits or ''
    return render_template('create_opp.html', title='تعديل الفرصة', form=form, opp=opp)


@opportunities.route("/opportunity/<int:opp_id>/delete", methods=['POST'])
@login_required
def delete_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(opp)
    db.session.commit()
    flash('تم حذف الفرصة بنجاح', 'info')
    return redirect(url_for('opportunities.home'))


@opportunities.route("/apply/<int:opp_id>", methods=['GET', 'POST'])
@login_required
def apply(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)

    # منع صاحب الفرصة من التقديم عليها
    if current_user.id == opp.user_id:
        flash('لا يمكنك التقديم على فرصة قمت بنشرها بنفسك', 'warning')
        return redirect(url_for('opportunities.opportunity_detail', opp_id=opp_id))

    # التحقق من عدم التقديم مرتين
    existing = Application.query.filter_by(user_id=current_user.id, opportunity_id=opp_id).first()
    if existing:
        flash('لقد تقدمت لهذه الفرصة مسبقاً', 'warning')
        return redirect(url_for('opportunities.opportunity_detail', opp_id=opp_id))

    if request.method == 'POST':
        new_app = Application(
            user_id=current_user.id,
            opportunity_id=opp_id,
            contact_email=request.form.get('contact_email', ''),
            contact_phone=request.form.get('contact_phone', ''),
            applicant_education=request.form.get('applicant_education', ''),
            applicant_experience=request.form.get('applicant_experience', ''),
            applicant_skills=request.form.get('applicant_skills', ''),
            current_position=request.form.get('current_position', ''),
            motivation=request.form.get('motivation', ''),
            relevant_experience=request.form.get('relevant_experience', ''),
            availability=request.form.get('availability', ''),
        )
        new_app.compatibility_score = calculate_compatibility(opp, new_app)
        db.session.add(new_app)
        db.session.commit()
        flash('تم تقديم طلبك بنجاح! سيتم مراجعته من قبل صاحب الفرصة.', 'success')
        return redirect(url_for('opportunities.my_applications'))
    return render_template('apply_form.html', title='التقديم على الفرصة', opp=opp)


@opportunities.route("/my-applications")
@login_required
def my_applications():
    user_apps = Application.query.filter_by(user_id=current_user.id)\
        .order_by(Application.date_applied.desc()).all()
    return render_template('my_applications.html', title='طلباتي', apps=user_apps)


@opportunities.route("/my-posts")
@login_required
def my_job_requests():
    my_opps = Opportunity.query.filter_by(user_id=current_user.id)\
        .order_by(Opportunity.date_posted.desc()).all()
    return render_template('job_requests.html', title='فرصي المنشورة', opportunities=my_opps)


@opportunities.route("/opportunity/<int:opp_id>/applicants")
@login_required
def view_applicants(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    if opp.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    apps = Application.query.filter_by(opportunity_id=opp_id)\
        .order_by(Application.compatibility_score.desc(), Application.date_applied.desc()).all()
    return render_template('view_applicants.html', title='المتقدمون', opp=opp, apps=apps)


@opportunities.route("/application/<int:app_id>/status", methods=['POST'])
@login_required
def update_application_status(app_id):
    application = Application.query.get_or_404(app_id)
    opp = application.opportunity
    if opp.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    new_status = request.form.get('status', 'pending')
    if new_status in ('pending', 'accepted', 'rejected'):
        application.status = new_status
        db.session.commit()
        status_text = {'accepted': 'قبول', 'rejected': 'رفض', 'pending': 'إعادة للمراجعة'}
        flash(f'تم {status_text[new_status]} طلب {application.applicant.username}', 'success')
    return redirect(url_for('opportunities.view_applicants', opp_id=opp.id))


@opportunities.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول إلى لوحة التحكم', 'danger')
        return redirect(url_for('opportunities.home'))

    edu_stats = db.session.query(
        User.education_level, func.count(User.id)
    ).group_by(User.education_level).all()

    type_stats = db.session.query(
        Opportunity.type, func.count(Opportunity.id)
    ).group_by(Opportunity.type).all()

    total_users = User.query.count()
    total_apps = Application.query.count()
    total_opps = Opportunity.query.count()
    recent_users = User.query.order_by(User.date_joined.desc()).limit(5).all()
    recent_apps = Application.query.order_by(Application.date_applied.desc()).limit(5).all()
    recent_opps = Opportunity.query.order_by(Opportunity.date_posted.desc()).limit(5).all()

    return render_template(
        'admin_dashboard.html',
        title='لوحة التحكم',
        edu_stats=edu_stats,
        type_stats=type_stats,
        total_users=total_users,
        total_apps=total_apps,
        total_opps=total_opps,
        recent_users=recent_users,
        recent_apps=recent_apps,
        recent_opps=recent_opps
    )


# ─── إدارة المستخدمين ───

@opportunities.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('opportunities.home'))

    search = request.args.get('q', '')
    role_filter = request.args.get('role', '')
    page = request.args.get('page', 1, type=int)

    query = User.query
    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )
    if role_filter:
        query = query.filter_by(role=role_filter)

    users = query.order_by(User.date_joined.desc()).paginate(page=page, per_page=20, error_out=False)
    total_users = User.query.count()
    total_admins = User.query.filter_by(role='admin').count()

    return render_template(
        'admin_users.html',
        title='إدارة المستخدمين',
        users=users,
        search=search,
        role_filter=role_filter,
        total_users=total_users,
        total_admins=total_admins
    )


@opportunities.route("/admin/users/<int:user_id>")
@login_required
def admin_user_detail(user_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول', 'danger')
        return redirect(url_for('opportunities.home'))

    user = User.query.get_or_404(user_id)
    user_apps = Application.query.filter_by(user_id=user_id).order_by(Application.date_applied.desc()).all()
    user_opps = Opportunity.query.filter_by(user_id=user_id).order_by(Opportunity.date_posted.desc()).all()

    return render_template(
        'admin_user_detail.html',
        title=f'المستخدم: {user.username}',
        user=user,
        user_apps=user_apps,
        user_opps=user_opps
    )


@opportunities.route("/admin/users/<int:user_id>/update", methods=['POST'])
@login_required
def admin_update_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = User.query.get_or_404(user_id)

    # منع تعديل الأدمن على نفسه من هذه الصفحة
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip()
    new_role = request.form.get('role', 'user')
    new_phone = request.form.get('phone', '').strip()

    if new_username and new_username != user.username:
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            flash('اسم المستخدم مستخدم بالفعل', 'danger')
            return redirect(url_for('opportunities.admin_user_detail', user_id=user_id))
        user.username = new_username

    if new_email and new_email != user.email:
        existing = User.query.filter_by(email=new_email).first()
        if existing:
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return redirect(url_for('opportunities.admin_user_detail', user_id=user_id))
        user.email = new_email

    if new_role in ('user', 'admin'):
        user.role = new_role

    user.phone = new_phone or None

    db.session.commit()
    flash(f'تم تحديث بيانات المستخدم {user.username} بنجاح', 'success')
    return redirect(url_for('opportunities.admin_user_detail', user_id=user_id))


@opportunities.route("/admin/users/<int:user_id>/delete", methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('opportunities.admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'تم حذف المستخدم {username} وجميع بياناته بنجاح', 'info')
    return redirect(url_for('opportunities.admin_users'))
