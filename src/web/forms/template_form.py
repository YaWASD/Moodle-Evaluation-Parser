"""
Формы для управления шаблонами оформления.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


QUESTION_TYPE_CHOICES = [
    ("essay_gigachat", "Развернутый ответ"),
    ("shortanswer", "Краткий ответ"),
    ("multichoice", "Множественный выбор"),
    ("matching", "Сопоставление"),
    ("truefalse", "Верно/Неверно"),
]


class TemplateForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    type = SelectField("Тип вопроса", choices=QUESTION_TYPE_CHOICES, validators=[DataRequired()])
    description = StringField("Описание")
    config = TextAreaField("Конфигурация (JSON)", default="{}")
    submit = SubmitField("Сохранить")


class TemplateImportForm(FlaskForm):
    payload = TextAreaField("JSON шаблона", validators=[DataRequired()])
    submit = SubmitField("Импортировать")

