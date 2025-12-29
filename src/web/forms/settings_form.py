"""
Настройки пользователя (сессия).
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField


class SettingsForm(FlaskForm):
    theme = SelectField(
        "Тема оформления",
        choices=[("light", "Светлая"), ("dark", "Тёмная")],
        default="light",
    )
    default_format = SelectField(
        "Формат экспорта по умолчанию",
        choices=[("docx", "DOCX"), ("pdf", "PDF"), ("html", "HTML"), ("markdown", "Markdown"), ("excel", "Excel")],
        default="docx",
    )
    submit = SubmitField("Сохранить настройки")


class ResetDataForm(FlaskForm):
    submit = SubmitField("Очистить данные")









