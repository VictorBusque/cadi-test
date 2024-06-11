import json
import re
from docx import Document
from docx.oxml.ns import qn

def is_paragraph_highlighted(paragraph):
    """
    Check if any part of a paragraph is highlighted.

    Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph to check.

    Returns:
    bool: True if any part of the paragraph is highlighted, False otherwise.
    """
    for run in paragraph.runs:
        # Access the underlying XML of the run
        rPr = run._element.xpath('.//w:rPr')
        if rPr:
            highlight = rPr[0].find(qn('w:highlight'))
            if highlight is not None:
                return True
    return False

def extract_questions(docx_path):
    document = Document(docx_path)
    questions = []

    correct_option_pattern = re.compile(r'\(pag\s*\d+\)$')

    current_question = None
    current_options = {}
    correct_option = None
    correct_content = None
    option_letters = ['a', 'b', 'c', 'd']
    option_index = 0

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()
        text = correct_option_pattern.sub('', text).strip()



        if len(text) > 100:
            current_question = None
            current_options = {}
            correct_option = None
            correct_content = None
        elif not current_question:
            continue

        if not current_question:
            current_question = text

        elif len(current_options) < 4:
            if text:
                current_options[option_letters[option_index]] = text
                option_index += 1
                if is_paragraph_highlighted(paragraph):
                    correct_option = option_letters[option_index - 1]
                    correct_content = correct_option_pattern.sub('', text).strip()
                if option_index == 4:
                    option_index = 0
                    if correct_option:
                        questions.append({
                            "topic": "Lote examen 2022",  # Add topic extraction logic if necessary
                            "question": current_question,
                            "options": current_options,
                            "correct": {
                                "option": correct_option,
                                "content": correct_content
                            }
                        })
                    current_question = None
                    current_options = {}
                    correct_option = None
                    correct_content = None

    return questions


def main():
    docx_path = 'data/EXAMENS CADI 2022.docx'
    questions = extract_questions(docx_path)
    json_output = json.dumps(questions, ensure_ascii=False, indent=4)

    with open('exam_2022_questions.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json_output)


if __name__ == '__main__':
    main()
