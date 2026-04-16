from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class OpportunityForm(FlaskForm):
    title = StringField('المسمى الوظيفي', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=5, max=150, message='يجب أن يكون العنوان بين 5 و 150 حرفاً')
    ])
    company = StringField('جهة العمل / المنظمة', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=2, max=100)
    ])
    type = SelectField('نوع الفرصة', choices=[
        ('وظيفة', 'وظيفة'),
        ('تدريب', 'تدريب تعاوني'),
        ('دورة', 'دورة تدريبية'),
        ('تطوع', 'عمل تطوعي'),
        ('تمهير', 'تمهير'),
        ('عمل حر', 'عمل حر / مستقل'),
    ], validators=[DataRequired(message='يرجى اختيار نوع الفرصة')])
    work_type = SelectField('نمط العمل', choices=[
        ('', 'غير محدد'),
        ('حضوري', 'حضوري'),
        ('عن بعد', 'عن بعد'),
        ('هجين', 'هجين'),
    ], validators=[Optional()])
    location = StringField('موقع العمل', validators=[
        Optional(), Length(max=100)
    ])
    salary_range = StringField('الراتب / المكافأة', validators=[
        Optional(), Length(max=100)
    ])
    gender_preference = SelectField('الجنس المطلوب', choices=[
        ('الجميع', 'الجميع'),
        ('ذكور', 'ذكور فقط'),
        ('إناث', 'إناث فقط'),
    ], validators=[Optional()])
    min_education = SelectField('الحد الأدنى للمؤهل', choices=[
        ('', 'غير محدد'),
        ('ثانوي', 'ثانوي'),
        ('دبلوم', 'دبلوم'),
        ('بكالوريوس', 'بكالوريوس'),
        ('ماجستير', 'ماجستير'),
        ('دكتوراه', 'دكتوراه'),
    ], validators=[Optional()])
    min_experience = SelectField('الخبرة المطلوبة', choices=[
        ('', 'غير محدد'),
        ('بدون خبرة', 'بدون خبرة (حديث تخرج)'),
        ('سنة أو أقل', 'سنة أو أقل'),
        ('1-3 سنوات', '1 - 3 سنوات'),
        ('3-5 سنوات', '3 - 5 سنوات'),
        ('+5 سنوات', 'أكثر من 5 سنوات'),
    ], validators=[Optional()])
    required_skills = StringField('المهارات المطلوبة', validators=[
        Optional(), Length(max=500)
    ])
    required_certifications = StringField('الشهادات المهنية المطلوبة', validators=[
        Optional(), Length(max=300)
    ])
    responsibilities = TextAreaField('المهام والمسؤوليات', validators=[
        Optional(), Length(max=3000)
    ])
    description = TextAreaField('وصف الفرصة والمتطلبات التفصيلية', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=20, message='يجب أن يكون الوصف 20 حرفاً على الأقل')
    ])
    benefits = TextAreaField('المزايا والتعويضات', validators=[
        Optional(), Length(max=2000)
    ])
    submit = SubmitField('نشر الفرصة')
