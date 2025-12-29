"""
Форма загрузки XML файлов.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, MultipleFileField
from wtforms import SubmitField


class UploadForm(FlaskForm):
    """Форма для загрузки XML файлов Moodle."""

    xml_file = MultipleFileField(
        "XML файлы Moodle",
        validators=[
            FileRequired(message="Выберите один или несколько XML файлов."),
            FileAllowed(["xml"], message="Допускаются только файлы с расширением .xml."),
        ],
    )
    submit = SubmitField("Загрузить и обработать")



