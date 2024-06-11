from datetime import datetime
from time import time

import streamlit as st
import json
import random

# Load questions from JSON file
with open('exam_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

with open("exam_2022_questions.json", "r", encoding="utf-8") as f:
    questions_2022 = json.load(f)

questions += questions_2022

NUM_Q = 10

exam_tab, docs_tab = st.tabs(["Examen", "Documentació"])
selected_doc = docs_tab.selectbox("Selecciona la documentació", ["Document 1", "Document 2", "Document 3"])
docs_tab.markdown("### Documentació")
docs_tab.write(f"Aquesta és la documentació que has seleccionat {selected_doc}.")

# Initialize session state
if 'current_question' not in st.session_state:
    # Select 20 random questions
    random.shuffle(questions)
    st.session_state["ph_time"] = 0
    st.session_state["current_time"] = 0
    st.session_state["question_list"] = questions
    st.session_state["current_question"] = 0
    st.session_state["answered_questions"] = 0
    st.session_state["answers"] = [None] * 20
    st.session_state["score"] = 0


def render_question(index: int):
    q = st.session_state["question_list"][index]
    exam_tab.write(f"### Tema: {q['topic']}")
    exam_tab.write(f"#### Pregunta {st.session_state['answered_questions'] + 1}: {q['question']}")

    options = list(q['options'].keys())
    answer = exam_tab.radio(
            label="Selecciona la teva resposta:",
            options=options,
            format_func=lambda x: q['options'][x]
    )
    return answer


if st.session_state["answered_questions"] < NUM_Q:
    curr_min = st.session_state["current_time"] / 60
    exam_tab.markdown(f"Tiempo invertido: {curr_min:.2f}/{NUM_Q} minutos.")

    t = datetime.utcnow().timestamp()
    if st.session_state["ph_time"] == 0:
        st.session_state["ph_time"] = t
    index = st.session_state["current_question"]
    q = st.session_state["question_list"][index]
    answer = render_question(index)

    if exam_tab.button("Seleccionar"):
        st.session_state["answers"][st.session_state["current_question"]] = answer
        exam_tab.info(f"Your answer: {q['options'][answer]}")
        if answer == q['correct']['option']:
            st.session_state["score"] += 1
        else:
            st.session_state["score"] -= 0.33
        st.session_state["current_time"] += datetime.utcnow().timestamp() - st.session_state["ph_time"]
        st.session_state["ph_time"] = 0
        st.session_state["current_question"] += 1
        st.session_state["answered_questions"] += 1
        st.rerun()
    elif exam_tab.button("Ignorar"):
        st.session_state["current_question"] += 1
        st.rerun()
    elif exam_tab.button("Passar"):
        st.session_state["answers"][st.session_state["current_question"]] = "Pass"
        st.session_state["current_time"] += datetime.utcnow().timestamp() - st.session_state["ph_time"]
        st.session_state["ph_time"] = 0
        st.session_state["current_question"] += 1
        st.session_state["answered_questions"] += 1
        st.rerun()


else:
    exam_tab.write(f"### La teva nota: {st.session_state.score}/{NUM_Q}")

    for i, q in enumerate(st.session_state["question_list"][:st.session_state["current_question"]]):
        if st.session_state['answers'][i] is None:
            exam_tab.write(f"### Pregunta {i + 1}: {q['question']}")
            exam_tab.info("### No has contestat a aquesta pregunta")
            continue
        exam_tab.write(f"#### Pregunta {i + 1}: {q['question']}")
        exam_tab.write(f"Resposta correcta: {q['options'][q['correct']['option']]}")
        if st.session_state['answers'][i] == q['correct']['option']:
            exam_tab.success("Correcte")
        elif st.session_state['answers'][i] == "Pass":
            exam_tab.warning("Passada")
        else:
            exam_tab.write(
                    f"La teva resposta: {q['options'][st.session_state['answers'][i]] if st.session_state['answers'][i] else 'No answer'}")
            exam_tab.error("Incorrecte")

exam_tab.write("---")
exam_tab.write("Note: Actualitza la pàgina per a tornar a començar.")
