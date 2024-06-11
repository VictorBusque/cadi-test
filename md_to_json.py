import re
import json

def parse_markdown(file_content):
    questions = []
    sections = file_content.split('---------------------')

    topic = None

    for section in sections:
        if section.strip():
            # Match the topic
            topic_match = re.search(r'# TEMA \d+ - (.+?)\n', section)
            if topic_match:
                topic = topic_match.group(1).strip()

            # Match the question
            question_match = re.search(r'## PREGUNTA \d+: (.+?)\n', section)
            if question_match:
                question_text = question_match.group(1).strip()

                # Match the options
                options = {}
                options_matches = re.findall(r'\* ([a-d])\) (.+?)\n', section)
                for option in options_matches:
                    options[option[0]] = option[1].strip()

                # Match the correct answer
                answer_match = re.search(r'### RESPOSTA: \(`([a-d])`\)', section)
                if answer_match:
                    correct_option = answer_match.group(1).strip()
                    correct_content_match = re.search(r'```\n(.+?)\n```', section, re.DOTALL)
                    if correct_content_match:
                        correct_content = correct_content_match.group(1).strip()
                    else:
                        correct_content = options[correct_option]

                    question_data = {
                        "topic": topic,
                        "question": question_text,
                        "options": options,
                        "correct": {
                            "option": correct_option,
                            "content": correct_content
                        }
                    }
                    questions.append(question_data)
    return questions

def markdown_to_json(input_filepath, output_filepath):
    with open(input_filepath, 'r', encoding='utf-8') as file:
        file_content = file.read()

    questions = parse_markdown(file_content)

    with open(output_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(questions, json_file, ensure_ascii=False, indent=4)

# Example usage:
input_filepath = '/Users/vbusque/personal/repos/exam_helper/results/EXAMENS.md'  # Replace with your input file path
output_filepath = 'exam_questions.json'  # Replace with your desired output file path

markdown_to_json(input_filepath, output_filepath)
