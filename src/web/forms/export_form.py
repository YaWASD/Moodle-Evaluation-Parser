"""
Форма экспорта документов.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class ExportForm(FlaskForm):
    courses = SelectMultipleField("Курсы", choices=[], validators=[DataRequired()], coerce=str)
    format = SelectField(
        "Формат",
        choices=[
            ("docx", "DOCX (Word)"),
            ("pdf", "PDF"),
            ("html", "HTML"),
            ("markdown", "Markdown"),
            ("excel", "Excel"),
        ],
        default="docx",
        validators=[DataRequired()],
    )
    template_name = SelectField(
        "Шаблон",
        choices=[
            ("standard", "Стандартный"),
        ],
        default="standard",
    )
    metadata_template = SelectField("Шаблон метаданных", choices=[], default="")
    # Поля ПК/ИПК могут быть пустыми (не всегда требуются в экспортируемом документе)
    pk_prefix = StringField("ПК префикс", default="ПК")
    pk_id = StringField("ПК ID", default="1.3")
    ipk_prefix = StringField("ИПК префикс", default="ИПК")
    ipk_id = StringField("ИПК ID", default="1.3.3")
    description = TextAreaField(
        "Описание компетенции",
        default="Устанавливает, настраивает и вводит в эксплуатацию серверные информационные системы и облачные сервисы",
    )
    submit = SubmitField("Сформировать документы")

