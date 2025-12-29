"""
Формы для работы с вопросами.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class QuestionForm(FlaskForm):
    course_id = SelectField("Курс", choices=[], validators=[DataRequired()])
    name = StringField("Название вопроса", validators=[DataRequired(), Length(max=255)])
    type = SelectField("Тип вопроса", choices=[], validators=[DataRequired()])
    question_text = TextAreaField("Текст вопроса", validators=[DataRequired()])
    reference_answer = TextAreaField("Эталонный ответ")
    answers = TextAreaField("Варианты ответов (по одному в строке)")
    correct_answers = TextAreaField("Правильные ответы (по одному в строке)")
    submit = SubmitField("Сохранить")



