from flask.ext.wtf import Form
from wtforms.fields import StringField
from wtforms.validators import DataRequired

class LoginForm(Form):
    name = StringField('name:', validators=[DataRequired()])

