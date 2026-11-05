"use strict";

const setupView = document.querySelector("#setup-view");
const questionView = document.querySelector("#question-view");
const resultsView = document.querySelector("#results-view");
const rangeForm = document.querySelector("#range-form");
const startSelect = document.querySelector("#start-verb");
const endSelect = document.querySelector("#end-verb");
const rangeSummary = document.querySelector("#range-summary");
const setupError = document.querySelector("#setup-error");
const loadError = document.querySelector("#load-error");
const answerForm = document.querySelector("#answer-form");
const answerError = document.querySelector("#answer-error");
const answerFeedback = document.querySelector("#answer-feedback");
const checkAnswerButton = document.querySelector("#check-answer");
const skipQuestionButton = document.querySelector("#skip-question");
const nextQuestionButton = document.querySelector("#next-question");

const answerFields = [
    { key: "BV", input: document.querySelector("#answer-bv") },
    { key: "V-ED", input: document.querySelector("#answer-past") },
    { key: "V-EN", input: document.querySelector("#answer-participle") },
];

let verbs = [];
let selectedVerbs = [];
let answers = [];
let currentIndex = 0;
let hasCheckedAnswer = false;

function showView(view) {
    setupView.hidden = view !== setupView;
    questionView.hidden = view !== questionView;
    resultsView.hidden = view !== resultsView;
}

function normalizeAnswer(value) {
    return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function getAcceptedAnswers(values) {
    return values.map(normalizeAnswer);
}

function updateRangeSummary() {
    if (!verbs.length || !startSelect.value || !endSelect.value) {
        return;
    }

    const first = Number(startSelect.value);
    const last = Number(endSelect.value);
    if (first > last) {
        rangeSummary.textContent = "Le premier verbe doit précéder le dernier dans la liste.";
        rangeSummary.classList.add("is-invalid");
        return;
    }

    rangeSummary.textContent = `${last - first + 1} verbe${last === first ? "" : "s"} à réviser`;
    rangeSummary.classList.remove("is-invalid");
}

function formatAcceptedAnswers(values) {
    return values.join(" / ");
}

function getTranslations(verb) {
    return verb.conjugations.translation.join(", ");
}

function updateProgress() {
    const completed = currentIndex;
    const percentage = Math.round((completed / selectedVerbs.length) * 100);
    document.querySelector("#quiz-progress").style.width = `${percentage}%`;
    document.querySelector("#quiz-progress-track").setAttribute("aria-valuenow", String(percentage));
    document.querySelector("#question-counter").textContent =
        `Verbe ${Math.min(currentIndex + 1, selectedVerbs.length)} / ${selectedVerbs.length}`;
}

function resetAnswerForm() {
    answerForm.reset();
    answerError.hidden = true;
    answerFeedback.hidden = true;
    answerFeedback.classList.remove("is-correct", "is-incorrect");
    hasCheckedAnswer = false;

    answerFields.forEach(({ input }) => {
        input.disabled = false;
        input.classList.remove("is-correct", "is-incorrect");
        input.removeAttribute("aria-invalid");
        input.nextElementSibling.textContent = "";
    });

    checkAnswerButton.hidden = false;
    nextQuestionButton.hidden = true;
}

function showQuestion() {
    if (currentIndex >= selectedVerbs.length) {
        showResults();
        return;
    }

    const verb = selectedVerbs[currentIndex];
    document.querySelector("#question-title").textContent = getTranslations(verb);
    resetAnswerForm();
    updateProgress();
    showView(questionView);
    answerFields[0].input.focus();
}

function buildResultItem(result) {
    const item = document.createElement("li");
    item.className = `result-item ${result.skipped ? "is-skipped" : result.mastered ? "is-mastered" : "needs-review"}`;

    const icon = document.createElement("span");
    icon.className = "result-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = result.skipped ? "→" : result.mastered ? "✓" : "↻";

    const details = document.createElement("span");
    details.className = "result-details";

    const verbName = document.createElement("strong");
    verbName.textContent = result.verb.name;

    const verbForms = document.createElement("span");
    verbForms.textContent = [
        result.verb.conjugations.BV[0],
        formatAcceptedAnswers(result.verb.conjugations["V-ED"]),
        formatAcceptedAnswers(result.verb.conjugations["V-EN"]),
    ].join(" · ");

    const status = document.createElement("span");
    status.className = "result-status";
    status.textContent = result.skipped ? "Passé" : result.mastered ? "Maîtrisé" : "À revoir";

    details.append(verbName, verbForms);
    item.append(icon, details, status);
    return item;
}

function showResults() {
    const mastered = answers.filter((answer) => answer.mastered).length;
    const total = answers.length;
    const percentage = Math.round((mastered / total) * 100);

    document.querySelector("#mastered-count").textContent = String(mastered);
    document.querySelector("#reviewed-count").textContent = String(total);
    document.querySelector("#score-percentage").textContent = `${percentage}%`;
    document.querySelector("#score-ring").style.setProperty("--score", `${percentage}%`);
    document.querySelector("#score-ring").setAttribute("aria-label", `Score de ${percentage} %`);
    document.querySelector("#results-range").textContent =
        `${selectedVerbs[0].name} → ${selectedVerbs[selectedVerbs.length - 1].name}`;

    const scoreMessage = document.querySelector("#score-message");
    if (percentage === 100) {
        scoreMessage.textContent = "Parfait, tu maîtrises toute cette série !";
    } else if (percentage >= 70) {
        scoreMessage.textContent = "Très bon travail, encore un petit effort !";
    } else if (percentage >= 40) {
        scoreMessage.textContent = "Tu progresses. Une nouvelle révision t'aidera !";
    } else {
        scoreMessage.textContent = "Continue à t'entraîner, ça va rentrer !";
    }

    const resultsList = document.querySelector("#results-list");
    resultsList.replaceChildren(...answers.map(buildResultItem));
    showView(resultsView);
    document.querySelector("#retry-quiz").focus();
}

function loadQuiz() {
    const firstIndex = verbs.findIndex((verb) => verb.index === Number(startSelect.value));
    const lastIndex = verbs.findIndex((verb) => verb.index === Number(endSelect.value));

    if (firstIndex < 0 || lastIndex < firstIndex) {
        setupError.textContent = "Choisis une plage valide : le premier verbe doit être avant le dernier.";
        setupError.hidden = false;
        return;
    }

    selectedVerbs = verbs.slice(firstIndex, lastIndex + 1);
    answers = [];
    currentIndex = 0;
    setupError.hidden = true;
    showQuestion();
}

function checkAnswer(event) {
    event.preventDefault();

    if (hasCheckedAnswer) {
        return;
    }

    const missingAnswer = answerFields.find(({ input }) => !input.value.trim());
    if (missingAnswer) {
        answerError.textContent = "Complète les trois formes avant de vérifier.";
        answerError.hidden = false;
        missingAnswer.input.focus();
        return;
    }

    answerError.hidden = true;
    const verb = selectedVerbs[currentIndex];
    let correctCount = 0;

    const submittedAnswers = answerFields.map(({ key, input }) => {
        const isCorrect = getAcceptedAnswers(verb.conjugations[key]).includes(normalizeAnswer(input.value));
        if (isCorrect) {
            correctCount += 1;
        }

        input.disabled = true;
        input.classList.add(isCorrect ? "is-correct" : "is-incorrect");
        input.setAttribute("aria-invalid", String(!isCorrect));
        input.nextElementSibling.textContent = isCorrect
            ? "Correct"
            : `Réponse : ${formatAcceptedAnswers(verb.conjugations[key])}`;

        return { key, value: input.value.trim(), isCorrect };
    });

    const mastered = correctCount === answerFields.length;
    answers.push({ verb, mastered, submittedAnswers });
    hasCheckedAnswer = true;

    answerFeedback.classList.toggle("is-correct", mastered);
    answerFeedback.classList.toggle("is-incorrect", !mastered);
    document.querySelector("#feedback-title").textContent = mastered ? "Verbe maîtrisé !" : "À revoir encore un peu";
    document.querySelector("#feedback-copy").textContent = mastered
        ? "Les trois formes sont correctes. Bien joué !"
        : "Compare tes réponses avec les bonnes formes ci-dessus, puis continue.";
    answerFeedback.hidden = false;
    checkAnswerButton.hidden = true;
    skipQuestionButton.hidden = true;
    nextQuestionButton.textContent = currentIndex === selectedVerbs.length - 1
        ? "Voir mon score"
        : "Verbe suivant";
    nextQuestionButton.hidden = false;
    nextQuestionButton.focus();
}

function skipQuestion() {
    if (hasCheckedAnswer) {
        return;
    }

    answers.push({
        verb: selectedVerbs[currentIndex],
        mastered: false,
        skipped: true,
        submittedAnswers: [],
    });
    currentIndex += 1;
    showQuestion();
}

async function loadVerbs() {
    try {
        const response = await fetch("data/verbs_list.json");
        if (!response.ok) {
            throw new Error(`Chargement des verbes impossible (HTTP ${response.status}).`);
        }

        const data = await response.json();
        verbs = Object.entries(data)
            .map(([name, value]) => ({
                name,
                index: Number(value.index),
                conjugations: value.conjugations,
            }))
            .sort((left, right) => left.index - right.index);

        if (
            !verbs.length ||
            verbs.some((verb) =>
                !Number.isInteger(verb.index) ||
                !["BV", "V-ED", "V-EN", "translation"].every(
                    (key) => Array.isArray(verb.conjugations[key]) && verb.conjugations[key].length > 0,
                ),
            )
        ) {
            throw new Error("La liste des verbes contient des données manquantes ou invalides.");
        }

        const options = verbs.map((verb) => {
            const option = document.createElement("option");
            option.value = String(verb.index);
            option.textContent = `${verb.index}. ${verb.name} — ${getTranslations(verb)}`;
            return option;
        });

        startSelect.replaceChildren(...options.map((option) => option.cloneNode(true)));
        endSelect.replaceChildren(...options);
        endSelect.value = String(verbs[verbs.length - 1].index);
        startSelect.disabled = false;
        endSelect.disabled = false;
        document.querySelector("#verb-total").textContent = String(verbs.length);
        document.querySelector("#start-button").disabled = false;
        updateRangeSummary();
    } catch (error) {
        console.error(error);
        loadError.hidden = false;
        rangeSummary.textContent = "La liste des verbes n'a pas pu être chargée.";
        rangeSummary.classList.add("is-invalid");
    }
}

rangeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadQuiz();
});

startSelect.addEventListener("change", updateRangeSummary);
endSelect.addEventListener("change", updateRangeSummary);

answerForm.addEventListener("submit", checkAnswer);

nextQuestionButton.addEventListener("click", () => {
    currentIndex += 1;
    showQuestion();
});

skipQuestionButton.addEventListener("click", skipQuestion);

document.querySelector("#back-to-setup").addEventListener("click", () => {
    showView(setupView);
    startSelect.focus();
});

document.querySelector("#retry-quiz").addEventListener("click", () => {
    showView(setupView);
    startSelect.focus();
});

loadVerbs();
