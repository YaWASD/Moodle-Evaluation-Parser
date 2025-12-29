"""
Форма для шаблонов метаданных.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class MetadataTemplateForm(FlaskForm):
    name = StringField("Название шаблона", validators=[DataRequired()])
    # Поля ПК/ИПК и описание могут быть пустыми — зависит от требований к документу
    pk_prefix = StringField("ПК префикс")
    pk_id = StringField("ПК ID")
    ipk_prefix = StringField("ИПК префикс")
    ipk_id = StringField("ИПК ID")
    description = TextAreaField("Описание компетенции")
    submit = SubmitField("Сохранить")





