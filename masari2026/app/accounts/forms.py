from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, NumberRange


class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=2, max=20, message='يجب أن يكون الاسم بين 2 و 20 حرفاً')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=6, message='يجب أن تكون كلمة المرور 6 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        EqualTo('password', message='كلمتا المرور غير متطابقتين')
    ])
    submit = SubmitField('إنشاء حساب')


class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    submit = SubmitField('تسجيل الدخول')


class ProfileForm(FlaskForm):
    skills = TextAreaField('المهارات الرئيسية (افصل بينها بفاصلة)', validators=[
        Optional()
    ])
    experience_years = IntegerField('سنوات الخبرة', validators=[
        Optional(),
        NumberRange(min=0, max=50, message='يرجى إدخال رقم صحيح بين 0 و 50')
    ])
    experience_desc = TextAreaField('تفاصيل الخبرات السابقة', validators=[Optional()])
    cv_link = StringField('رابط السيرة الذاتية (Google Drive / Dropbox)', validators=[
        Optional(),
        URL(message='يرجى إدخال رابط صحيح يبدأ بـ http أو https')
    ])
    submit = SubmitField('حفظ التعديلات')
