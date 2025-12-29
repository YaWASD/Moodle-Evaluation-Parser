"""Управление стилями документов Word"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


class DocumentStyles:
    """Класс для настройки стилей документа"""
    
    @staticmethod
    def setup_styles(doc: Document, style_config: dict | None = None):
        """
        Настройка стилей документа
        
        Args:
            doc: Объект документа Word
            style_config: необязательные переопределения стилей из шаблона
        """
        styles = doc.styles
        
        # Стиль заголовка документа
        DocumentStyles._setup_title_style(styles, style_config)
        
        # Стиль заголовка вопроса
        DocumentStyles._setup_question_header_style(styles, style_config)
        
        # Стиль текста вопроса
        DocumentStyles._setup_question_text_style(styles, style_config)
        
        # Стиль текста в таблице ответов
        DocumentStyles._setup_answer_text_style(styles, style_config)
    
    @staticmethod
    def _setup_title_style(styles, style_config: dict | None = None):
        """Настройка стиля заголовка документа"""
        try:
            title_style = styles.add_style('CustomTitle', 1)
        except:
            title_style = styles['CustomTitle']
        
        title_style.font.name = 'Times New Roman'
        size = (style_config or {}).get("title_size")
        title_style.font.size = Pt(int(size)) if isinstance(size, (int, float)) else Pt(22)
        title_style.font.color.rgb = DocumentStyles._rgb_from_hex('#000000')
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    @staticmethod
    def _setup_question_header_style(styles, style_config: dict | None = None):
        """Настройка стиля заголовка вопроса"""
        try:
            question_header_style = styles.add_style('QuestionHeader', 1)
        except:
            question_header_style = styles['QuestionHeader']
        
        question_header_style.font.name = 'Times New Roman'
        size = (style_config or {}).get("header_size")
        question_header_style.font.size = Pt(int(size)) if isinstance(size, (int, float)) else Pt(16)
        color = (style_config or {}).get("header_color")
        question_header_style.font.color.rgb = DocumentStyles._rgb_from_hex(color) if isinstance(color, str) and color.strip() else DocumentStyles._rgb_from_hex('#C00000')
        question_header_style.font.italic = True
        question_header_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        question_header_style.paragraph_format.space_before = Pt(12)
        question_header_style.paragraph_format.space_after = Pt(0)
        question_header_style.paragraph_format.line_spacing = 1.0
        question_header_style.paragraph_format.left_indent = Pt(0)
        question_header_style.paragraph_format.right_indent = Pt(0)
    
    @staticmethod
    def _setup_question_text_style(styles, style_config: dict | None = None):
        """Настройка стиля текста вопроса"""
        try:
            question_text_style = styles.add_style('Question', 1)
        except:
            question_text_style = styles['Question']
        
        question_text_style.font.name = 'Times New Roman'
        size = (style_config or {}).get("body_size")
        question_text_style.font.size = Pt(int(size)) if isinstance(size, (int, float)) else Pt(14)
        question_text_style.font.color.rgb = DocumentStyles._rgb_from_hex("#000000")
        question_text_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        question_text_style.paragraph_format.space_before = Pt(0)
        question_text_style.paragraph_format.space_after = Pt(0)
        question_text_style.paragraph_format.line_spacing = 1.0
        question_text_style.paragraph_format.left_indent = Pt(0)
        question_text_style.paragraph_format.right_indent = Pt(0)
    
    @staticmethod
    def _setup_answer_text_style(styles, style_config: dict | None = None):
        """Настройка стиля текста в таблице ответов"""
        try:
            answer_style = styles.add_style('AnswerText', 1)
        except:
            answer_style = styles['AnswerText']
        
        answer_style.font.name = 'Times New Roman'
        size = (style_config or {}).get("answer_size")
        answer_style.font.size = Pt(int(size)) if isinstance(size, (int, float)) else Pt(12)
        answer_style.font.color.rgb = DocumentStyles._rgb_from_hex("#000000")
        answer_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        answer_style.paragraph_format.space_before = Pt(0)
        answer_style.paragraph_format.space_after = Pt(6)
        answer_style.paragraph_format.line_spacing = 1.0
        answer_style.paragraph_format.left_indent = Pt(0)
        answer_style.paragraph_format.right_indent = Pt(0)
    
    @staticmethod
    def _rgb_from_hex(hex_color: str) -> RGBColor:
        """
        Конвертация HEX цвета в RGBColor объект
        
        Args:
            hex_color: HEX цвет (например, '#C00000')
            
        Returns:
            RGBColor объект
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return RGBColor(r, g, b)

