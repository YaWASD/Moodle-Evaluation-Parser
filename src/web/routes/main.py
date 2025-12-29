"""
Основные маршруты веб-приложения.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from src.generators.document_generator import DocumentGenerator
from src.generators.exporters import ExcelExporter, HTMLExporter, MarkdownExporter, PDFExporter
from src.models.metadata import DocumentMetadata
from src.models.question import Question
from src.parsers.xml_parser import XMLParser
from src.utils.file_utils import sanitize_filename

from ..forms.export_form import ExportForm
from ..forms.metadata_template_form import MetadataTemplateForm
from ..forms.question_form import QuestionForm
from ..forms.simple import DeleteForm
from ..forms.template_form import TemplateForm, TemplateImportForm
from ..forms.settings_form import ResetDataForm, SettingsForm
from ..forms.upload_form import UploadForm
from ..utils import history, metadata_storage, session_manager as sm, statistics as stats_utils, template_storage, validator
from ..utils.template_defaults import default_config
from src.template_engine.migration import migrate_v1_to_v2
from src.template_engine.presets import presets_for_type, preset_table_default
from src.template_engine.render_html import render_document_html, render_question_html
from src.template_engine.validator import validate_template_config_v2
from ..utils.storage import load_snapshot, save_snapshot


main_bp = Blueprint("main", __name__)


@dataclass
class UploadMeta:
    id: str
    original_name: str
    stored_name: str
    uploaded_at: str
    course_count: int
    question_count: int


def _get_uploads() -> List[dict]:
    return session.get("uploads", [])


def _append_upload(meta: UploadMeta) -> None:
    uploads = _get_uploads()
    uploads.append(asdict(meta))
    session["uploads"] = uploads


def _get_exports() -> List[dict]:
    return session.get("exports", [])


def _append_export(data: dict) -> None:
    exports = _get_exports()
    exports.append(data)
    session["exports"] = exports
    session.modified = True


@main_bp.route("/", methods=["GET"])
def index():
    snapshots = _all_snapshots()
    uploads = _get_uploads()
    exports = _get_exports()

    combined = {
        "questions": [q for s in snapshots for q in (s.get("questions") or [])],
        "courses": [c for s in snapshots for c in (s.get("courses") or [])],
    }
    stats = stats_utils.overall_stats(combined, uploads)
    stats["generated_reports"] = len(exports)
    stats["total_uploads"] = len(uploads)
    return render_template("index.html", stats=stats)


@main_bp.route("/upload", methods=["GET", "POST"])
def upload():
    form = UploadForm()
    uploads = _get_uploads()

    if form.validate_on_submit():
        files = form.xml_file.data or []
        processed: list[str] = []
        failed: list[str] = []

        for file in files:
            file_id = str(uuid4())
            original_name = (getattr(file, "filename", None) or "").strip() or "questions.xml"
            safe_name = secure_filename(original_name) or f"{file_id}.xml"
            stored_name = f"{file_id}_{safe_name}"
            upload_path = Path(current_app.config["UPLOAD_FOLDER"]) / stored_name
            upload_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                file.save(upload_path)
                parser = XMLParser(str(upload_path))
                courses = parser.parse_courses()
            except Exception:  # pylint: disable=broad-except
                current_app.logger.exception("Ошибка при парсинге XML файла")
                upload_path.unlink(missing_ok=True)
                failed.append(original_name)
                continue

            courses_payload: list[dict] = []
            all_questions: list[dict] = []

            for course_index, course in enumerate(courses):
                course_name = course.name or f"Курс {course_index + 1}"
                questions_payload = []

                for question_index, question in enumerate(course.questions):
                    question_dict = question.to_dict()
                    question_id = f"{file_id}:{course_index}:{question_index}"
                    payload = {
                        "id": question_id,
                        "course_id": f"{file_id}:{course_index}",
                        "course_name": course_name,
                        "type": question_dict.get("type", ""),
                        "name": question_dict.get("name", "") or f"Вопрос {question_index + 1}",
                        "question_text": question_dict.get("question_text", ""),
                        "reference_answer": question_dict.get("reference_answer", ""),
                        "answers": question_dict.get("answers", []),
                        "correct_answers": question_dict.get("correct_answers", []),
                        "matching_items": question_dict.get("matching_items", []),
                        "matching_answers": question_dict.get("matching_answers", []),
                    }
                    questions_payload.append(payload)
                    all_questions.append(payload)

                courses_payload.append(
                    {
                        "id": f"{file_id}:{course_index}",
                        "name": course_name,
                        "question_count": len(questions_payload),
                        "questions": questions_payload,
                    }
                )

            snapshot = {
                "id": file_id,
                "original_name": original_name,
                "stored_name": stored_name,
                "uploaded_at": datetime.utcnow().isoformat(),
                "course_count": len(courses_payload),
                "question_count": len(all_questions),
                "courses": courses_payload,
                "questions": all_questions,
            }
            save_snapshot(file_id, snapshot)

            _append_upload(
                UploadMeta(
                    id=file_id,
                    original_name=original_name,
                    stored_name=stored_name,
                    uploaded_at=snapshot["uploaded_at"],
                    course_count=snapshot["course_count"],
                    question_count=snapshot["question_count"],
                )
            )
            processed.append(file_id)
            history.log("Upload", f"Файл {original_name} обработан")

        session.modified = True

        if not processed:
            flash("Не удалось обработать XML файлы. Проверьте их структуру.", "error")
            return render_template("upload.html", form=form, uploads=uploads), 400

        if failed:
            flash(f"Обработано: {len(processed)}. Ошибка обработки: {len(failed)}.", "warning")
        else:
            flash(f"Файлов обработано: {len(processed)}.", "success")

        # Текущим считаем последний успешно обработанный
        last_id = processed[-1]
        sm.set_current_file(last_id)

        # Если файлов несколько — показываем историю загрузок, иначе — страницу результатов
        if len(processed) > 1:
            return redirect(url_for("main.files_history"))
        return redirect(url_for("main.parse_results", file_id=last_id))

    return render_template("upload.html", form=form, uploads=uploads)


@main_bp.get("/files")
def files_history():
    uploads = list(reversed(_get_uploads()))
    return render_template("files_history.html", uploads=uploads)


@main_bp.get("/parse_results/<file_id>")
def parse_results(file_id: str):
    snapshot = load_snapshot(file_id)
    if not snapshot:
        flash("Результаты обработки не найдены. Перезагрузите файл.", "error")
        return redirect(url_for("main.upload"))
    sm.set_current_file(file_id)
    return render_template("parse_results.html", snapshot=snapshot)


QUESTION_TYPE_LABELS = {
    "essay_gigachat": "Развернутый ответ",
    "shortanswer": "Краткий ответ",
    "multichoice": "Множественный выбор",
    "matching": "Сопоставление",
    "truefalse": "Верно/Неверно",
}


def _ensure_snapshot():
    snapshot = sm.get_snapshot()
    if not snapshot:
        flash("Сначала загрузите XML файл для обработки.", "error")
        return None
    return snapshot


def _all_snapshots() -> list[dict]:
    """
    Возвращает список снапшотов по всем загруженным файлам в текущей сессии.
    """
    snapshots: list[dict] = []
    for u in _get_uploads():
        fid = u.get("id")
        if not fid:
            continue
        s = load_snapshot(fid)
        if s:
            snapshots.append(s)
    return snapshots


def _combined_snapshot() -> dict:
    snapshots = _all_snapshots()
    return {
        "questions": [q for s in snapshots for q in (s.get("questions") or [])],
        "courses": [c for s in snapshots for c in (s.get("courses") or [])],
    }


def _find_course_any(course_id: str) -> dict | None:
    if not course_id:
        return None
    # course_id = <file_id>:<course_index>
    file_id = course_id.split(":", 1)[0] if ":" in course_id else None
    if file_id:
        snapshot = load_snapshot(file_id)
        if snapshot:
            found = next((c for c in snapshot.get("courses", []) if c.get("id") == course_id), None)
            if found:
                return found
    # fallback: search all
    for s in _all_snapshots():
        found = next((c for c in s.get("courses", []) if c.get("id") == course_id), None)
        if found:
            return found
    return None


@main_bp.get("/questions")
def questions():
    snapshots = _all_snapshots()
    if not snapshots:
        flash("Сначала загрузите XML файл для обработки.", "error")
        return redirect(url_for("main.upload"))

    questions_data: list[dict] = []
    courses: list[dict] = []
    for s in snapshots:
        file_name = s.get("original_name", "")
        for q in s.get("questions", []) or []:
            q2 = dict(q)
            q2["file_name"] = file_name
            questions_data.append(q2)
        courses.extend(s.get("courses", []) or [])

    filter_type = request.args.get("type", "")
    filter_course = request.args.get("course", "")
    search = request.args.get("search", "").strip()
    use_regex = request.args.get("regex", "0") == "1"
    has_answers = request.args.get("has_answers", "")

    filtered = questions_data
    if filter_type:
        filtered = [q for q in filtered if q["type"] == filter_type]
    if filter_course:
        filtered = [q for q in filtered if q["course_id"] == filter_course]
    if has_answers == "1":
        filtered = [q for q in filtered if q.get("answers")]
    if search:
        if use_regex:
            try:
                pattern = re.compile(search, re.IGNORECASE)
                filtered = [
                    q for q in filtered if pattern.search(q["name"]) or pattern.search(q["question_text"])
                ]
            except re.error:
                flash("Некорректное регулярное выражение.", "error")
        else:
            lowered = search.lower()
            filtered = [
                q for q in filtered if lowered in q["name"].lower() or lowered in q["question_text"].lower()
            ]

    return render_template(
        "questions.html",
        questions=filtered,
        filters={
            "type": filter_type,
            "course": filter_course,
            "search": request.args.get("search", ""),
            "regex": "1" if use_regex else "0",
            "has_answers": has_answers,
        },
        courses=courses,
        question_types=QUESTION_TYPE_LABELS,
    )


@main_bp.get("/questions/<question_id>")
def question_detail(question_id: str):
    snapshot = _ensure_snapshot()
    if not snapshot:
        return redirect(url_for("main.upload"))

    question = sm.get_question(question_id)
    if not question:
        flash("Вопрос не найден.", "error")
        return redirect(url_for("main.questions"))

    return render_template(
        "question_detail.html",
        question=question,
        type_label=QUESTION_TYPE_LABELS.get(question["type"], question["type"]),
    )


@main_bp.route("/questions/<question_id>/edit", methods=["GET", "POST"])
def question_edit(question_id: str):
    snapshot = _ensure_snapshot()
    if not snapshot:
        return redirect(url_for("main.upload"))

    question = sm.get_question(question_id)
    if not question:
        flash("Вопрос не найден.", "error")
        return redirect(url_for("main.questions"))

    form = QuestionForm()
    form.course_id.choices = [(course["id"], course["name"]) for course in snapshot.get("courses", [])]
    form.type.choices = [(key, value) for key, value in QUESTION_TYPE_LABELS.items()]
    question_issues = validator.validate_question(question)

    if not form.is_submitted():
        form.course_id.data = question["course_id"]
        form.name.data = question["name"]
        form.type.data = question["type"]
        form.question_text.data = question["question_text"]
        form.reference_answer.data = question.get("reference_answer", "")
        form.answers.data = "\n".join(question.get("answers", []))
        form.correct_answers.data = "\n".join(question.get("correct_answers", []))

    if form.validate_on_submit():
        updated = {
            "name": form.name.data.strip(),
            "type": form.type.data,
            "question_text": form.question_text.data.strip(),
            "reference_answer": form.reference_answer.data.strip(),
            "answers": _split_lines(form.answers.data),
            "correct_answers": _split_lines(form.correct_answers.data),
        }
        sm.update_question(question_id, updated)
        history.log("Question update", f"Обновлен вопрос {question['name']}")
        flash("Вопрос обновлен.", "success")
        return redirect(url_for("main.question_detail", question_id=question_id))

    return render_template(
        "question_edit.html",
        form=form,
        question=question,
        readonly_course=True,
        issues=question_issues,
    )


@main_bp.route("/questions/create", methods=["GET", "POST"])
def question_create():
    snapshot = _ensure_snapshot()
    if not snapshot:
        return redirect(url_for("main.upload"))

    form = QuestionForm()
    course_choices = [(course["id"], course["name"]) for course in snapshot.get("courses", [])]
    form.course_id.choices = course_choices
    form.type.choices = [(key, value) for key, value in QUESTION_TYPE_LABELS.items()]

    if not course_choices:
        flash("В текущем файле нет курсов для добавления вопросов.", "error")
        return redirect(url_for("main.upload"))

    if form.validate_on_submit():
        course_id = form.course_id.data
        course = next((c for c in snapshot.get("courses", []) if c["id"] == course_id), None)
        if not course:
            flash("Выбранный курс не найден.", "error")
            return redirect(url_for("main.questions"))

        new_question_index = len(course.get("questions", []))
        question_id = f"{course_id}:{new_question_index}"
        payload = {
            "id": question_id,
            "course_id": course_id,
            "course_name": course["name"],
            "type": form.type.data,
            "name": form.name.data.strip(),
            "question_text": form.question_text.data.strip(),
            "reference_answer": form.reference_answer.data.strip(),
            "answers": _split_lines(form.answers.data),
            "correct_answers": _split_lines(form.correct_answers.data),
            "matching_items": [],
            "matching_answers": [],
        }
        sm.add_question(course_id, payload)
        history.log("Question create", f"Добавлен вопрос {payload['name']}")
        flash("Вопрос добавлен.", "success")
        return redirect(url_for("main.questions"))

    return render_template("question_create.html", form=form)


@main_bp.get("/questions/bulk_edit")
def questions_bulk_edit():
    return render_template("questions_bulk_edit.html")


@main_bp.get("/preview/<question_id>")
def question_preview(question_id: str):
    snapshot = _ensure_snapshot()
    if not snapshot:
        return redirect(url_for("main.upload"))

    question = sm.get_question(question_id)
    if not question:
        flash("Вопрос не найден.", "error")
        return redirect(url_for("main.questions"))

    return render_template(
        "question_preview.html",
        question=question,
        type_label=QUESTION_TYPE_LABELS.get(question["type"], question["type"]),
    )


@main_bp.get("/courses")
def courses():
    combined = _combined_snapshot()
    courses_data = combined.get("courses", [])
    for course in courses_data:
        course["type_stats"] = _type_stats(course.get("questions", []))

    return render_template(
        "courses.html",
        courses=courses_data,
        total_questions=len(combined.get("questions", []) or []),
        type_labels=QUESTION_TYPE_LABELS,
    )


@main_bp.get("/courses/<course_id>")
def course_detail(course_id: str):
    course = _find_course_any(course_id)
    if not course:
        flash("Курс не найден.", "error")
        return redirect(url_for("main.courses"))

    questions = course.get("questions", [])
    return render_template(
        "course_detail.html",
        course=course,
        questions=questions,
        type_stats=_type_stats(questions),
        type_labels=QUESTION_TYPE_LABELS,
    )


@main_bp.get("/categories")
def categories():
    categories_payload = []
    for course in (_combined_snapshot().get("courses", []) or []):
        categories_payload.append(
            {
                "path": f"$module$/top/Оценочные материалы/{course['name']}",
                "course_name": course["name"],
                "question_count": course.get("question_count", 0),
            }
        )

    return render_template("categories.html", categories=categories_payload)


@main_bp.route("/templates", methods=["GET", "POST"])
def templates_list():
    templates = template_storage.list_templates()
    import_form = TemplateImportForm()
    delete_form = DeleteForm()

    if import_form.validate_on_submit():
        try:
            payload = json.loads(import_form.payload.data)
        except json.JSONDecodeError:
            flash("Некорректный JSON. Проверьте синтаксис.", "error")
        else:
            template_storage.import_template(payload)
            flash("Шаблон импортирован.", "success")
            history.log("Template import", f"Импортирован шаблон {payload.get('name', 'без названия')}")
            return redirect(url_for("main.templates_list"))

    return render_template(
        "templates_list.html",
        templates=templates,
        template_sets=_group_templates_by_name(templates),
        import_form=import_form,
        delete_form=delete_form,
        question_types=QUESTION_TYPE_LABELS,
    )


def _group_templates_by_name(templates: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for tpl in templates:
        name = (tpl.get("name") or "").strip() or "Без названия"
        grouped.setdefault(name, []).append(tpl)
    sets = []
    for name in sorted(grouped.keys(), key=lambda s: s.lower()):
        items = sorted(grouped[name], key=lambda t: (t.get("type") or "", t.get("updated_at") or ""))
        # Важно: не использовать ключ "items", чтобы не конфликтовать с dict.items в Jinja
        sets.append({"name": name, "templates": items})
    return sets


@main_bp.route("/templates/create", methods=["GET", "POST"])
def template_create():
    form = TemplateForm()
    if not form.is_submitted():
        # MVP1: стартуем с v2 preset (таблица/список), но оставляем поддержку старого v1.
        try:
            form.config.data = json.dumps(preset_table_default(form.type.data), ensure_ascii=False, indent=2)
        except Exception:
            form.config.data = "{}"
    if form.validate_on_submit():
        if not _is_valid_json(form.config.data):
            flash("Конфигурация должна быть в формате JSON.", "error")
        else:
            schema_version = None
            try:
                parsed = json.loads(form.config.data.strip() or "{}")
                schema_version = parsed.get("version")
            except Exception:
                pass
            template_storage.save_template(
                {
                    "name": form.name.data.strip(),
                    "type": form.type.data,
                    "description": form.description.data.strip(),
                    "config": form.config.data.strip() or "{}",
                    "schema_version": schema_version,
                }
            )
            flash("Шаблон создан.", "success")
            history.log("Template create", f"Создан шаблон {form.name.data.strip()}")
            return redirect(url_for("main.templates_list"))
    return render_template(
        "template_edit.html",
        form=form,
        title="Новый шаблон",
        presets=presets_for_type(form.type.data),
        questions=_get_preview_questions(),
    )


@main_bp.route("/templates/<template_id>/edit", methods=["GET", "POST"])
def template_edit(template_id: str):
    template = template_storage.get_template(template_id)
    if not template:
        flash("Шаблон не найден.", "error")
        return redirect(url_for("main.templates_list"))

    form = TemplateForm()
    if not form.is_submitted():
        form.name.data = template["name"]
        form.type.data = template["type"]
        form.description.data = template.get("description", "")
        form.config.data = template.get("config", "{}")
        # Если шаблон создан раньше и config пустой — подставим дефолт.
        if form.config.data.strip() in {"", "{}", "null"}:
            try:
                form.config.data = json.dumps(preset_table_default(form.type.data), ensure_ascii=False, indent=2)
            except Exception:
                form.config.data = "{}"

    if form.validate_on_submit():
        if not _is_valid_json(form.config.data):
            flash("Конфигурация должна быть в формате JSON.", "error")
        else:
            schema_version = None
            try:
                parsed = json.loads(form.config.data.strip() or "{}")
                schema_version = parsed.get("version")
            except Exception:
                pass
            template_storage.update_template(
                template_id,
                {
                    "name": form.name.data.strip(),
                    "type": form.type.data,
                    "description": form.description.data.strip(),
                    "config": form.config.data.strip() or "{}",
                    "schema_version": schema_version,
                },
            )
            flash("Шаблон обновлен.", "success")
            history.log("Template update", f"Обновлен шаблон {form.name.data.strip()}")
            return redirect(url_for("main.templates_list"))

    return render_template(
        "template_edit.html",
        form=form,
        title="Редактирование шаблона",
        presets=presets_for_type(form.type.data),
        questions=_get_preview_questions(),
    )


def _get_preview_questions() -> list[dict]:
    snapshot = sm.get_snapshot()
    if not snapshot:
        return []
    # ограничим, чтобы не раздувать страницу
    return (snapshot.get("questions") or [])[:200]


@main_bp.post("/templates/preview")
def template_preview():
    """
    Живой предпросмотр шаблона: принимает JSON {type, config}.
    Возвращает HTML (используем `srcdoc` в iframe на странице редактирования).
    """
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return Response("Bad JSON", status=400, mimetype="text/plain")

    q_type = (payload.get("type") or "").strip()
    mode = (payload.get("mode") or "").strip() or "export_html"
    config_raw = payload.get("config")
    if isinstance(config_raw, str):
        try:
            config = json.loads(config_raw) if config_raw.strip() else {}
        except json.JSONDecodeError:
            return Response("Invalid template config JSON", status=400, mimetype="text/plain")
    elif isinstance(config_raw, dict):
        config = config_raw
    else:
        config = {}

    question_id = (payload.get("question_id") or "").strip()
    selected_question = sm.get_question(question_id) if question_id else None

    # если старый v1 или пусто — мигрируем/подставим пресет
    if not config:
        config = preset_table_default(q_type)
    elif config.get("version") != 2:
        config = migrate_v1_to_v2(config, q_type)

    # В режиме v2 проверяем blocks-схему; в режиме export_html — не обязательно.
    if mode == "v2":
        errors = validate_template_config_v2(config)
        if errors:
            return Response("Template invalid: " + "; ".join(errors), status=400, mimetype="text/plain")

    # Sample question per type
    sample_by_type = {
        "essay_gigachat": Question(
            type="essay_gigachat",
            question_text="Опишите принцип работы TCP.",
            reference_answer="TCP — протокол транспортного уровня с установлением соединения.",
            name="sample_essay",
        ),
        "shortanswer": Question(
            type="shortanswer",
            question_text="Столица Франции?",
            reference_answer="Париж",
            name="sample_short",
            correct_answers=["Париж"],
        ),
        "multichoice": Question(
            type="multichoice",
            question_text="Выберите простые числа.",
            reference_answer="",
            name="sample_multi",
            answers=["2", "3", "4"],
            correct_answers=["2", "3"],
        ),
        "matching": Question(
            type="matching",
            question_text="Сопоставьте термин и определение.",
            reference_answer="",
            name="sample_match",
            matching_items=[
                {"item": "CPU", "answer": "Центральный процессор"},
                {"item": "RAM", "answer": "Оперативная память"},
            ],
            matching_answers=["Оперативная память", "Центральный процессор"],
        ),
        "truefalse": Question(
            type="truefalse",
            question_text="HTTP — протокол прикладного уровня.",
            reference_answer="",
            name="sample_tf",
            answers=["Верно", "Неверно"],
            correct_answers=["Верно"],
        ),
    }

    sample = sample_by_type.get(q_type) or next(iter(sample_by_type.values()))
    question_dict = selected_question or sample.to_dict()
    question_dict.setdefault("type", q_type)
    metadata = DocumentMetadata(
        pk_prefix="ПК",
        pk_id="1.3",
        ipk_prefix="ИПК",
        ipk_id="1.3.3",
        description="Пример метаданных для предпросмотра",
        document_title="Предпросмотр шаблона",
    )

    if mode == "v2":
        # v2 blocks
        templates_by_type = {t: preset_table_default(t) for t in QUESTION_TYPE_LABELS.keys()}
        if q_type:
            templates_by_type[q_type] = config
        html_text = render_document_html(
            questions=[question_dict],
            metadata=metadata.to_dict() | {"document_title": metadata.document_title},
            templates_by_type=templates_by_type,
            title="Предпросмотр шаблона",
        )
        return Response(html_text, mimetype="text/html")

    # export_html: как реальный экспорт HTMLExporter (как в output/*.html)
    # Поддерживаем v1 конфиги (styles/layout) и best-effort v2->v1 (styles + table widths).
    def _v2_to_v1_min(cfg2: dict, qt: str) -> dict:
        v1 = {"version": 1, "styles": {}, "layout": {}}
        if isinstance(cfg2.get("styles"), dict):
            v1["styles"] = cfg2["styles"]
        # берём ширины из первого table блока, если есть
        widths = None
        for b in cfg2.get("blocks") or []:
            if isinstance(b, dict) and b.get("kind") == "table":
                w = b.get("col_widths_pct")
                if isinstance(w, list) and all(isinstance(x, int) for x in w):
                    widths = w
                break
        if widths and qt:
            v1["layout"][qt] = {"table_cols_pct": widths}
        return v1

    try:
        from src.generators.exporters.html_exporter import HTMLExporter  # local import to avoid circulars
    except Exception:
        return Response("HTML exporter unavailable", status=500, mimetype="text/plain")

    q_obj = sample
    if selected_question:
        try:
            q_obj = Question.from_dict(selected_question)
        except Exception:
            q_obj = sample

    tpl_map = None
    if q_type and isinstance(config, dict):
        cfg_for_type = config
        if cfg_for_type.get("version") == 2:
            cfg_for_type = _v2_to_v1_min(cfg_for_type, q_type)
        tpl_map = {q_type: cfg_for_type}

    exporter = HTMLExporter()
    html_text, _meta = exporter.render_html([q_obj], metadata, template_map=tpl_map)
    return Response(html_text, mimetype="text/html")


@main_bp.post("/templates/<template_id>/delete")
def template_delete(template_id: str):
    form = DeleteForm()
    if form.validate_on_submit():
        deleted = template_storage.delete_template(template_id)
        flash("Шаблон удален." if deleted else "Шаблон не найден.", "success" if deleted else "error")
        if deleted:
            history.log("Template delete", f"Удален шаблон {template_id}")
    return redirect(url_for("main.templates_list"))


@main_bp.get("/templates/<template_id>/export")
def template_export(template_id: str):
    template = template_storage.get_template(template_id)
    if not template:
        flash("Шаблон не найден.", "error")
        return redirect(url_for("main.templates_list"))
    response = Response(json.dumps(template, ensure_ascii=False, indent=2), mimetype="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename=template_{template_id}.json"
    return response


EXPORTER_CLASSES = {
    "pdf": PDFExporter(),
    "html": HTMLExporter(),
    "markdown": MarkdownExporter(),
    "excel": ExcelExporter(),
}


@main_bp.route("/export", methods=["GET", "POST"])
def export():
    combined = _combined_snapshot()
    courses = combined.get("courses", [])
    form = ExportForm()
    form.courses.choices = [(course["id"], course["name"]) for course in courses]
    # На GET и при первом заходе поле может быть None, а шаблон ожидает итерируемое значение.
    form.courses.data = form.courses.data or []

    # Шаблоны выбираются как "набор" по имени: один выбор -> несколько конфигов по типам.
    # Это позволяет применять набор шаблонов ко всем типам вопросов в одном файле.
    all_templates = template_storage.list_templates()
    sets: dict[str, set[str]] = {}
    for tpl in all_templates:
        name = (tpl.get("name") or "").strip() or "Без названия"
        t = (tpl.get("type") or "").strip()
        sets.setdefault(name, set())
        if t:
            sets[name].add(t)
    template_choices = [("standard", "Стандартный")]
    for name in sorted(sets.keys(), key=lambda s: s.lower()):
        types = sorted(sets[name])
        label = name if not types else f"{name} (типов: {len(types)})"
        template_choices.append((name, label))
    form.template_name.choices = template_choices

    metadata_templates = metadata_storage.list_templates()
    form.metadata_template.choices = [("", "Без шаблона")] + [
        (tpl["id"], tpl["name"]) for tpl in metadata_templates
    ]

    if not courses:
        flash("Нет курсов для экспорта. Загрузите файл.", "error")
        return render_template("export.html", form=form, courses=courses, exports=_get_exports())

    # Применение шаблона метаданных без валидации основного экспорта
    if request.method == "POST" and request.form.get("apply_template"):
        template_id = form.metadata_template.data
        if template_id:
            template = metadata_storage.get_template(template_id)
            if template:
                _apply_metadata_template(form, template)
                flash("Шаблон метаданных применен.", "success")
            else:
                flash("Шаблон метаданных не найден.", "error")
        else:
            flash("Выберите шаблон метаданных.", "error")
        return render_template(
            "export.html",
            form=form,
            courses=courses,
            exports=list(reversed(_get_exports())),
        )

    if form.validate_on_submit():
        selected_ids = form.courses.data
        selected_courses = [course for course in courses if course["id"] in selected_ids]

        if not selected_courses:
            flash("Выберите хотя бы один курс.", "error")
        else:
            generated = []
            for course in selected_courses:
                questions_raw = course.get("questions", [])
                if not questions_raw:
                    continue
                questions = [Question.from_dict(q) for q in questions_raw]
                metadata = DocumentMetadata(
                    pk_prefix=form.pk_prefix.data.strip(),
                    pk_id=form.pk_id.data.strip(),
                    ipk_prefix=form.ipk_prefix.data.strip(),
                    ipk_id=form.ipk_id.data.strip(),
                    description=form.description.data.strip(),
                    document_title=course["name"],
                )

                timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                sanitized_name = sanitize_filename(f"{course['name']}_{timestamp}")
                format_choice = form.format.data
                output_folder = Path(current_app.config["OUTPUT_FOLDER"])
                output_folder.mkdir(parents=True, exist_ok=True)
                output_path = output_folder / f"{sanitized_name}.{format_choice}"

                generated_successfully = False

                # Пытаемся применить выбранный набор шаблонов (если не "standard")
                template_map = None
                selected_set_name = (form.template_name.data or "").strip()
                selected_cfg_by_type: dict[str, dict] = {}
                if selected_set_name and selected_set_name != "standard":
                    matching = [t for t in all_templates if (t.get("name") or "").strip() == selected_set_name]
                    for tpl in matching:
                        try:
                            cfg = json.loads(tpl.get("config", "{}") or "{}")
                        except json.JSONDecodeError:
                            cfg = {}
                        if cfg and tpl.get("type"):
                            selected_cfg_by_type[str(tpl.get("type"))] = cfg

                    # Если в наборе есть только один тип (legacy), применяем его ко всем типам в курсе
                    if len(selected_cfg_by_type) == 1:
                        only_cfg = next(iter(selected_cfg_by_type.values()))
                        course_types = sorted({(q.get("type") or "") for q in questions_raw if q.get("type")})
                        selected_cfg_by_type = {t: only_cfg for t in course_types}

                    if selected_cfg_by_type:
                        template_map = selected_cfg_by_type

                # MVP1: если HTML и v2-шаблон — используем новый движок с блоками.
                # Для HTML поддерживаем v2-конфиги по каждому типу.
                any_v2 = any(isinstance(cfg, dict) and cfg.get("version") == 2 for cfg in selected_cfg_by_type.values())
                if format_choice == "html" and any_v2:
                    # дефолтные пресеты для всех типов, которые встретились в курсе
                    templates_by_type = {}
                    for q in questions_raw:
                        q_type = q.get("type", "")
                        if q_type and q_type not in templates_by_type:
                            templates_by_type[q_type] = preset_table_default(q_type)
                    # переопределяем типы, для которых есть выбранные v2-конфиги
                    for t, cfg in selected_cfg_by_type.items():
                        if isinstance(cfg, dict) and cfg.get("version") == 2:
                            templates_by_type[t] = cfg
                    html_text = render_document_html(
                        questions=questions_raw,
                        metadata=metadata.to_dict() | {"document_title": metadata.document_title},
                        templates_by_type=templates_by_type,
                        title=course["name"],
                    )
                    output_path.write_text(html_text, encoding="utf-8")
                    generated_successfully = True
                elif format_choice == "docx":
                    generator = DocumentGenerator(metadata)
                    try:
                        result = generator.generate(questions, str(output_path), template_map=template_map)
                        generated_successfully = True
                        skipped = result.get("skipped_types") or {}
                        if skipped:
                            skipped_msg = ", ".join(f"{k}: {v}" for k, v in skipped.items())
                            flash(
                                f"Часть вопросов пропущена (нет шаблона): {skipped_msg}",
                                "warning",
                            )
                        errs = result.get("errors") or []
                        if errs:
                            flash(
                                f"Сформирован документ, но с ошибками рендеринга: {len(errs)}",
                                "warning",
                            )
                    except Exception as e:
                        current_app.logger.exception("DOCX export failed for course=%s", course.get("name"))
                        history.log("Export failed", f"DOCX: {course.get('name', '')}: {e}")
                        flash(f"Ошибка экспорта DOCX для курса '{course['name']}': {e}", "error")
                        continue
                else:
                    exporter = EXPORTER_CLASSES.get(format_choice)
                    if exporter:
                        try:
                            exporter.export(questions, metadata, str(output_path), template_map=template_map)
                            generated_successfully = True
                        except NotImplementedError:
                            flash(
                                f"Экспорт в формат {format_choice.upper()} пока недоступен, используйте DOCX.",
                                "info",
                            )
                            continue
                        except Exception as e:
                            current_app.logger.exception(
                                "Export failed: format=%s course=%s", format_choice, course.get("name")
                            )
                            history.log(
                                "Export failed",
                                f"{format_choice.upper()}: {course.get('name', '')}: {e}",
                            )
                            flash(
                                f"Ошибка экспорта {format_choice.upper()} для курса '{course['name']}': {e}",
                                "error",
                            )
                            continue
                    else:
                        flash(f"Неизвестный формат {format_choice}.", "error")
                        continue

                if not generated_successfully:
                    continue

                record = {
                    "id": str(uuid4()),
                    "course_name": course["name"],
                    "format": format_choice,
                    "filename": output_path.name,
                    "path": str(output_path),
                    "created_at": datetime.utcnow().isoformat(),
                }
                _append_export(record)
                generated.append(record)

            if generated:
                flash(f"Сформировано документов: {len(generated)}", "success")
                return redirect(url_for("main.exports_history"))
            flash("Не удалось сформировать документы. Проверьте выбранные курсы.", "error")

    return render_template(
        "export.html",
        form=form,
        courses=courses,
        exports=list(reversed(_get_exports())),
    )


@main_bp.get("/exports")
def exports_history():
    return render_template("export_history.html", exports=list(reversed(_get_exports())))


@main_bp.get("/exports/<export_id>/download")
def export_download(export_id: str):
    """
    Скачивание ранее сгенерированного файла экспорта (из текущей сессии).
    """
    exports = _get_exports()
    record = next((item for item in exports if item.get("id") == export_id), None)
    if not record:
        flash("Экспорт не найден (возможно, очищена сессия).", "error")
        return redirect(url_for("main.export"))

    output_root = Path(current_app.config["OUTPUT_FOLDER"]).resolve()
    # Берём путь из записи, но защищаемся от подмены/выхода из папки output
    candidate = Path(record.get("path") or (output_root / (record.get("filename") or ""))).resolve()
    if output_root not in candidate.parents and candidate != output_root:
        abort(400)
    if not candidate.exists() or not candidate.is_file():
        flash("Файл экспорта не найден на сервере.", "error")
        return redirect(url_for("main.export"))

    return send_file(candidate, as_attachment=True, download_name=candidate.name)


@main_bp.get("/activity")
def activity():
    return render_template("history.html", history_items=list(reversed(history.list_history())))


@main_bp.get("/statistics")
def statistics():
    combined = _combined_snapshot()
    if not (combined.get("courses") or combined.get("questions")):
        return redirect(url_for("main.upload"))
    stats = stats_utils.overall_stats(combined, _get_uploads())
    return render_template(
        "statistics.html",
        stats=stats,
        uploads=_get_uploads(),
        question_types=QUESTION_TYPE_LABELS,
    )


@main_bp.get("/statistics/course/<course_id>")
def statistics_course(course_id: str):
    course = _find_course_any(course_id)
    if not course:
        flash("Курс не найден.", "error")
        return redirect(url_for("main.statistics"))
    stats = stats_utils.course_stats(course)
    return render_template(
        "statistics_course.html",
        course=course,
        stats=stats,
        type_labels=QUESTION_TYPE_LABELS,
    )


@main_bp.get("/statistics/report")
def statistics_report():
    combined = _combined_snapshot()
    if not (combined.get("courses") or combined.get("questions")):
        return redirect(url_for("main.upload"))
    csv_data = stats_utils.build_csv_report(combined)
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=statistics_report.csv"
    return response


@main_bp.get("/statistics/course/<course_id>/export")
def statistics_course_export(course_id: str):
    course = _find_course_any(course_id)
    if not course:
        flash("Курс не найден.", "error")
        return redirect(url_for("main.statistics"))
    lines = ["Question Name,Type"]
    for question in course.get("questions", []):
        lines.append(f"{question['name']},{question['type']}")
    response = Response("\n".join(lines), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=course_{course_id}_report.csv"
    return response


@main_bp.get("/validation")
def validation():
    combined = _combined_snapshot()
    if not (combined.get("courses") or combined.get("questions")):
        return redirect(url_for("main.upload"))
    issues = validator.validate_snapshot(combined)
    return render_template("validation.html", issues=issues)


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    form = SettingsForm()
    reset_form = ResetDataForm()
    preferences = session.get("preferences", {"theme": session.get("theme", "light"), "default_format": "docx"})
    if not form.is_submitted():
        form.theme.data = preferences.get("theme", "light")
        form.default_format.data = preferences.get("default_format", "docx")

    if form.validate_on_submit():
        session["theme"] = form.theme.data
        session["preferences"] = {
            "theme": form.theme.data,
            "default_format": form.default_format.data,
        }
        session.modified = True
        history.log("Settings", f"Тема: {form.theme.data}, Формат: {form.default_format.data}")
        flash("Настройки сохранены.", "success")
        return redirect(url_for("main.settings"))

    return render_template("settings.html", form=form, reset_form=reset_form)


@main_bp.post("/settings/reset")
def settings_reset():
    """
    Очищает временные данные: загрузки, результаты парсинга, экспорты, историю действий.
    Настройки (тема/формат по умолчанию) сохраняются.
    """
    form = ResetDataForm()
    if not form.validate_on_submit():
        flash("Не удалось выполнить очистку данных.", "error")
        return redirect(url_for("main.settings"))

    # Очистка файлов
    for key in ("UPLOAD_FOLDER", "OUTPUT_FOLDER", "TEMP_FOLDER"):
        folder = Path(current_app.config[key])
        try:
            folder.mkdir(parents=True, exist_ok=True)
            for p in folder.iterdir():
                if p.is_file():
                    p.unlink(missing_ok=True)
        except Exception:  # pylint: disable=broad-except
            current_app.logger.exception("Failed to purge folder: %s", folder)

    # Очистка сессионных данных
    for k in ("uploads", "exports", "history", "current_file_id"):
        session.pop(k, None)
    session.modified = True

    history.log("Reset", "Очищены временные данные (uploads/output/temp) и сессия")
    flash("Временные данные очищены.", "success")
    return redirect(url_for("main.settings"))


def _split_lines(value: str | None) -> list[str]:
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


def _type_stats(questions: list[dict]) -> dict[str, int]:
    stats: dict[str, int] = {}
    for question in questions:
        stats[question["type"]] = stats.get(question["type"], 0) + 1
    return stats


def _is_valid_json(value: str | None) -> bool:
    if not value:
        return True
    try:
        json.loads(value)
        return True
    except json.JSONDecodeError:
        return False


def _apply_metadata_template(form: ExportForm, template: dict) -> None:
    form.pk_prefix.data = template["pk_prefix"]
    form.pk_id.data = template["pk_id"]
    form.ipk_prefix.data = template["ipk_prefix"]
    form.ipk_id.data = template["ipk_id"]
    form.description.data = template["description"]


@main_bp.get("/metadata/templates")
def metadata_templates():
    templates = metadata_storage.list_templates()
    delete_form = DeleteForm()
    return render_template("metadata_templates.html", templates=templates, delete_form=delete_form)


@main_bp.route("/metadata/templates/create", methods=["GET", "POST"])
def metadata_template_create():
    form = MetadataTemplateForm()
    if form.validate_on_submit():
        metadata_storage.create_template(
            {
                "name": form.name.data.strip(),
                "pk_prefix": form.pk_prefix.data.strip(),
                "pk_id": form.pk_id.data.strip(),
                "ipk_prefix": form.ipk_prefix.data.strip(),
                "ipk_id": form.ipk_id.data.strip(),
                "description": form.description.data.strip(),
            }
        )
        flash("Шаблон метаданных создан.", "success")
        history.log("Metadata template create", f"Создан шаблон {form.name.data.strip()}")
        return redirect(url_for("main.metadata_templates"))
    return render_template("metadata_template_edit.html", form=form, title="Новый шаблон метаданных")


@main_bp.route("/metadata/templates/<template_id>/edit", methods=["GET", "POST"])
def metadata_template_edit(template_id: str):
    template = metadata_storage.get_template(template_id)
    if not template:
        flash("Шаблон не найден.", "error")
        return redirect(url_for("main.metadata_templates"))

    form = MetadataTemplateForm()
    if not form.is_submitted():
        form.name.data = template["name"]
        form.pk_prefix.data = template["pk_prefix"]
        form.pk_id.data = template["pk_id"]
        form.ipk_prefix.data = template["ipk_prefix"]
        form.ipk_id.data = template["ipk_id"]
        form.description.data = template["description"]

    if form.validate_on_submit():
        metadata_storage.update_template(
            template_id,
            {
                "name": form.name.data.strip(),
                "pk_prefix": form.pk_prefix.data.strip(),
                "pk_id": form.pk_id.data.strip(),
                "ipk_prefix": form.ipk_prefix.data.strip(),
                "ipk_id": form.ipk_id.data.strip(),
                "description": form.description.data.strip(),
            },
        )
        flash("Шаблон обновлен.", "success")
        history.log("Metadata template update", f"Обновлен шаблон {form.name.data.strip()}")
        return redirect(url_for("main.metadata_templates"))

    return render_template("metadata_template_edit.html", form=form, title="Редактирование шаблона метаданных")


@main_bp.post("/metadata/templates/<template_id>/delete")
def metadata_template_delete(template_id: str):
    form = DeleteForm()
    if form.validate_on_submit():
        deleted = metadata_storage.delete_template(template_id)
        flash("Шаблон удален." if deleted else "Шаблон не найден.", "success" if deleted else "error")
        if deleted:
            history.log("Metadata template delete", f"Удален шаблон {template_id}")
    return redirect(url_for("main.metadata_templates"))

