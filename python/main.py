import json
import random

from browser import ajax, console, document, html


KNOWN_FORMS = ("translation", "BV", "V-ED", "V-EN")
KNOWN_FORM_LABELS = {
    "translation": "traduction française",
    "BV": "base verbale",
    "V-ED": "prétérit",
    "V-EN": "participe passé",
}

verbs = []
selected_verbs = []
answers = []
current_index = 0
has_checked_answer = False
known_mode = "fixed"
fixed_known_form = "translation"
current_known_form = "translation"

answer_fields = [
    ("BV", "answer-bv", "status-bv"),
    ("V-ED", "answer-past", "status-past"),
    ("V-EN", "answer-participle", "status-participle"),
    ("translation", "answer-translation", "status-translation"),
]


def show_view(view_id):
    for candidate in ("setup-view", "question-view", "results-view"):
        document[candidate].hidden = candidate != view_id


def normalize_answer(value):
    return " ".join(value.strip().lower().split())


def accepted_answers(values):
    return [normalize_answer(value) for value in values]


def get_translations(verb):
    return ", ".join(verb["conjugations"]["translation"])


def format_answers(values):
    return " / ".join(values)


def set_class(element, class_name, active):
    classes = element.class_name.split()
    if active and class_name not in classes:
        classes.append(class_name)
    elif not active and class_name in classes:
        classes.remove(class_name)
    element.class_name = " ".join(classes)


def update_range_summary(*_args):
    if not verbs:
        return

    start_value = document["start-verb"].value
    end_value = document["end-verb"].value
    if not start_value or not end_value:
        return

    first = int(start_value)
    last = int(end_value)
    summary = document["range-summary"]
    if first > last:
        summary.text = "Le premier verbe doit précéder le dernier dans la liste."
        set_class(summary, "is-invalid", True)
        return

    count = sum(1 for verb in verbs if first <= verb["index"] <= last)
    suffix = "s" if count != 1 else ""
    summary.text = "{} verbe{} à réviser".format(count, suffix)
    set_class(summary, "is-invalid", False)


def update_progress():
    total = len(selected_verbs)
    percentage = round(current_index * 100 / total)
    document["quiz-progress"].style.width = "{}%".format(percentage)
    document["quiz-progress-track"].setAttribute("aria-valuenow", str(percentage))
    displayed_index = min(current_index + 1, total)
    document["question-counter"].text = "Verbe {} / {}".format(displayed_index, total)


def reset_answer_form():
    global has_checked_answer

    for key, input_id, status_id in answer_fields:
        answer_input = document[input_id]
        is_known = key == current_known_form
        document["field-group-{}".format(key)].hidden = is_known
        answer_input.required = not is_known
        answer_input.value = ""
        answer_input.disabled = False
        answer_input.removeAttribute("aria-invalid")
        set_class(answer_input, "is-correct", False)
        set_class(answer_input, "is-incorrect", False)
        document[status_id].text = ""

    document["answer-error"].hidden = True
    document["answer-feedback"].hidden = True
    set_class(document["answer-feedback"], "is-correct", False)
    set_class(document["answer-feedback"], "is-incorrect", False)
    document["check-answer"].hidden = False
    document["skip-question"].hidden = False
    document["next-question"].hidden = True
    has_checked_answer = False


def show_question():
    global current_known_form

    if current_index >= len(selected_verbs):
        show_results()
        return

    verb = selected_verbs[current_index]
    if known_mode == "random":
        current_known_form = random.choice(KNOWN_FORMS)
    else:
        current_known_form = fixed_known_form

    document["question-kicker"].text = "FORME CONNUE · {}".format(
        KNOWN_FORM_LABELS[current_known_form].upper()
    )
    document["question-title"].text = format_answers(
        verb["conjugations"][current_known_form]
    )
    reset_answer_form()
    update_progress()
    show_view("question-view")
    document["answer-bv"].focus()


def build_result_item(result):
    if result["skipped"]:
        result_class = "is-skipped"
        icon_text = "→"
        status_text = "Passé"
    elif result["mastered"]:
        result_class = "is-mastered"
        icon_text = "✓"
        status_text = "Maîtrisé"
    else:
        result_class = "needs-review"
        icon_text = "↻"
        status_text = "À revoir"

    verb = result["verb"]
    conjugations = verb["conjugations"]
    forms = " · ".join((
        conjugations["BV"][0],
        format_answers(conjugations["V-ED"]),
        format_answers(conjugations["V-EN"]),
    ))

    icon = html.SPAN(Class="result-icon")
    icon.text = icon_text
    icon.attrs["aria-hidden"] = "true"
    verb_name = html.STRONG()
    verb_name.text = verb["name"]
    verb_forms = html.SPAN()
    verb_forms.text = forms
    details = html.SPAN(Class="result-details")
    details <= verb_name
    details <= verb_forms
    status = html.SPAN(Class="result-status")
    status.text = status_text
    item = html.LI(Class="result-item {}".format(result_class))
    item <= icon
    item <= details
    item <= status
    return item


def show_results():
    mastered = sum(1 for answer in answers if answer["mastered"])
    total = len(answers)
    percentage = round(mastered * 100 / total)

    document["mastered-count"].text = str(mastered)
    document["reviewed-count"].text = str(total)
    document["score-percentage"].text = "{}%".format(percentage)
    document["score-ring"].style.background = (
        "conic-gradient(#9fc66c {}%, #e9eee2 {}%)".format(percentage, percentage)
    )
    document["score-ring"].setAttribute("aria-label", "Score de {} %".format(percentage))
    document["results-range"].text = "{} → {}".format(
        selected_verbs[0]["name"],
        selected_verbs[-1]["name"],
    )

    if percentage == 100:
        message = "Parfait, tu maîtrises toute cette série !"
    elif percentage >= 70:
        message = "Très bon travail, encore un petit effort !"
    elif percentage >= 40:
        message = "Tu progresses. Une nouvelle révision t'aidera !"
    elif percentage > 0:
        message = "Chaque réponse juste est un progrès. Continue à t'entraîner !"
    else:
        message = "Tu n'as pas encore maîtrisé de verbe dans cette série. Tu peux réessayer !"
    document["score-message"].text = message

    results_list = document["results-list"]
    results_list.clear()
    for answer in answers:
        results_list <= build_result_item(answer)

    show_view("results-view")
    document["retry-quiz"].focus()


def start_quiz(event):
    global selected_verbs, answers, current_index, known_mode, fixed_known_form

    event.preventDefault()
    first = int(document["start-verb"].value)
    last = int(document["end-verb"].value)
    setup_error = document["setup-error"]

    if first > last:
        setup_error.text = "Choisis une plage valide : le premier verbe doit être avant le dernier."
        setup_error.hidden = False
        return

    selected_verbs = [
        verb for verb in verbs
        if first <= verb["index"] <= last
    ]
    if not selected_verbs:
        setup_error.text = "Aucun verbe n'a été trouvé dans cette plage."
        setup_error.hidden = False
        return

    answers = []
    current_index = 0
    known_mode = document["known-mode"].value
    fixed_known_form = document["known-form"].value
    setup_error.hidden = True
    show_question()


def check_answer(event):
    global has_checked_answer

    event.preventDefault()
    if has_checked_answer:
        return

    missing_field = None
    required_fields = [
        field for field in answer_fields
        if field[0] != current_known_form
    ]
    for key, input_id, _ in required_fields:
        if not document[input_id].value.strip():
            missing_field = input_id
            break

    if missing_field:
        document["answer-error"].text = "Complète les trois réponses avant de vérifier."
        document["answer-error"].hidden = False
        document[missing_field].focus()
        return

    document["answer-error"].hidden = True
    verb = selected_verbs[current_index]
    correct_count = 0

    for key, input_id, status_id in required_fields:
        answer_input = document[input_id]
        is_correct = normalize_answer(answer_input.value) in accepted_answers(
            verb["conjugations"][key]
        )
        if is_correct:
            correct_count += 1

        answer_input.disabled = True
        answer_input.setAttribute("aria-invalid", str(not is_correct).lower())
        set_class(answer_input, "is-correct", is_correct)
        set_class(answer_input, "is-incorrect", not is_correct)
        if is_correct:
            document[status_id].text = "Correct"
        else:
            document[status_id].text = "Réponse : {}".format(
                format_answers(verb["conjugations"][key])
            )

    mastered = correct_count == len(required_fields)
    answers.append({
        "verb": verb,
        "mastered": mastered,
        "skipped": False,
    })
    has_checked_answer = True

    feedback = document["answer-feedback"]
    set_class(feedback, "is-correct", mastered)
    set_class(feedback, "is-incorrect", not mastered)
    if mastered:
        document["feedback-title"].text = "Verbe maîtrisé !"
        document["feedback-copy"].text = "Les trois formes sont correctes. Bien joué !"
    else:
        document["feedback-title"].text = "À revoir encore un peu"
        document["feedback-copy"].text = (
            "Compare tes réponses avec les bonnes formes ci-dessus, puis continue."
        )
    feedback.hidden = False

    document["check-answer"].hidden = True
    document["skip-question"].hidden = True
    next_button = document["next-question"]
    if current_index == len(selected_verbs) - 1:
        next_button.text = "Voir mon score →"
    else:
        next_button.text = "Verbe suivant →"
    next_button.hidden = False
    next_button.focus()


def skip_question(event):
    global current_index

    event.preventDefault()
    if has_checked_answer:
        return

    answers.append({
        "verb": selected_verbs[current_index],
        "mastered": False,
        "skipped": True,
    })
    current_index += 1
    show_question()


def next_question(event):
    global current_index

    event.preventDefault()
    current_index += 1
    show_question()


def return_to_setup(event):
    event.preventDefault()
    show_view("setup-view")
    document["start-verb"].focus()


def update_known_mode(*_args):
    is_random = document["known-mode"].value == "random"
    known_form_group = document["known-form-group"]
    known_form_group.hidden = is_random
    document["known-form"].disabled = is_random
    if is_random:
        document["known-mode-description"].text = (
            "Une forme différente est tirée au hasard pour chaque verbe ; "
            "tu complèteras les autres."
        )
    else:
        document["known-mode-description"].text = (
            "La forme choisie sera affichée pour chaque verbe ; tu complèteras les autres."
        )


def on_verbs_loaded(request):
    global verbs

    if request.status != 200:
        show_load_error("Le chargement de la liste des verbes a échoué (HTTP {}).".format(
            request.status
        ))
        return

    try:
        data = request.json
        loaded_verbs = []
        for name, value in data.items():
            conjugations = value["conjugations"]
            if not all(
                isinstance(conjugations.get(key), list) and conjugations[key]
                for key in ("BV", "V-ED", "V-EN", "translation")
            ):
                raise ValueError("Formes manquantes pour le verbe « {} ».".format(name))

            loaded_verbs.append({
                "name": name,
                "index": int(value["index"]),
                "conjugations": conjugations,
            })

        verbs = sorted(loaded_verbs, key=lambda verb: verb["index"])
        if not verbs or len({verb["index"] for verb in verbs}) != len(verbs):
            raise ValueError("La liste des verbes est vide ou contient des numéros en double.")

        document["start-verb"].clear()
        document["end-verb"].clear()
        for verb in verbs:
            option_text = "{}. {} — {}".format(
                verb["index"],
                verb["name"],
                get_translations(verb),
            )
            start_option = html.OPTION(value=str(verb["index"]))
            start_option.text = option_text
            end_option = html.OPTION(value=str(verb["index"]))
            end_option.text = option_text
            document["start-verb"] <= start_option
            document["end-verb"] <= end_option

        document["end-verb"].value = str(verbs[-1]["index"])
        document["start-verb"].disabled = False
        document["end-verb"].disabled = False
        document["verb-total"].text = str(len(verbs))
        document["start-button"].disabled = False
        update_range_summary()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        console.error(error)
        show_load_error("La liste des verbes est invalide : {}".format(error))


def show_load_error(message):
    document["load-error"].text = message
    document["load-error"].hidden = False
    document["range-summary"].text = "La liste des verbes n'a pas pu être chargée."
    set_class(document["range-summary"], "is-invalid", True)


document["start-verb"].bind("change", update_range_summary)
document["end-verb"].bind("change", update_range_summary)
document["known-mode"].bind("change", update_known_mode)
document["range-form"].bind("submit", start_quiz)
document["answer-form"].bind("submit", check_answer)
document["skip-question"].bind("click", skip_question)
document["next-question"].bind("click", next_question)
document["back-to-setup"].bind("click", return_to_setup)
document["retry-quiz"].bind("click", return_to_setup)

ajax.get("data/verbs_list.json", mode="json", oncomplete=on_verbs_loaded)