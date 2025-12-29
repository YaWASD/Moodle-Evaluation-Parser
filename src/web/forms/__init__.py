"""Пакет для форм Flask-WTF."""

from .question_form import QuestionForm  # noqa: F401
from .upload_form import UploadForm  # noqa: F401
from .export_form import ExportForm  # noqa: F401
from .template_form import TemplateForm, TemplateImportForm  # noqa: F401
from .metadata_template_form import MetadataTemplateForm  # noqa: F401
from .simple import DeleteForm  # noqa: F401
from .settings_form import SettingsForm  # noqa: F401


