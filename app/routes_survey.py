from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .models import Answer, Question, Response, Survey, User, db

survey_bp = Blueprint("survey", __name__, url_prefix="/inicio")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@survey_bp.route("/")
@login_required
def index():
    user = User.query.get(session["user_id"])
    surveys = Survey.query.filter_by(is_active=True).all()
    open_surveys = []
    for s in surveys:
        already_responded = Response.query.filter_by(
            user_id=user.id, survey_id=s.id, is_complete=True
        ).first()
        open_surveys.append(
            {
                "survey": s,
                "is_open": s.is_open,
                "already_responded": already_responded is not None,
            }
        )
    return render_template("survey/index.html", user=user, surveys=open_surveys)


@survey_bp.route("/<int:survey_id>/terminos")
@login_required
def terms(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    user = User.query.get(session["user_id"])

    if not survey.terms_text:
        return redirect(url_for("survey.take", survey_id=survey_id))

    existing = Response.query.filter_by(
        user_id=user.id, survey_id=survey_id, is_complete=True
    ).first()
    if existing:
        flash("Ya respondiste esta encuesta.", "info")
        return redirect(url_for("survey.index"))

    if not survey.is_open:
        flash("Esta encuesta no está disponible actualmente.", "warning")
        return redirect(url_for("survey.index"))

    return render_template("survey/terms.html", survey=survey, user=user)


@survey_bp.route("/<int:survey_id>")
@login_required
def take(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    user = User.query.get(session["user_id"])

    # Si tiene T&C, verificar que vengan del flujo de aceptación
    if survey.terms_text and not session.get(f"tc_accepted_{survey_id}"):
        return redirect(url_for("survey.terms", survey_id=survey_id))

    # Check already responded
    existing = Response.query.filter_by(
        user_id=user.id, survey_id=survey_id, is_complete=True
    ).first()
    if existing:
        flash("Ya respondiste esta encuesta.", "info")
        return redirect(url_for("survey.index"))

    # Check dates
    if not survey.is_open:
        flash("Esta encuesta no está disponible actualmente.", "warning")
        return redirect(url_for("survey.index"))

    questions = (
        Question.query.filter_by(survey_id=survey_id, parent_question_id=None)
        .order_by(Question.order)
        .all()
    )

    return render_template("survey/take.html", survey=survey, questions=questions, user=user)


@survey_bp.route("/<int:survey_id>/submit", methods=["POST"])
@login_required
def submit(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    user = User.query.get(session["user_id"])

    # Guard: already responded
    existing = Response.query.filter_by(
        user_id=user.id, survey_id=survey_id, is_complete=True
    ).first()
    if existing:
        flash("Ya respondiste esta encuesta.", "info")
        return redirect(url_for("survey.index"))

    if not survey.is_open:
        flash("Esta encuesta ya no está disponible.", "warning")
        return redirect(url_for("survey.index"))

    # Validate required fields
    all_questions = Question.query.filter_by(survey_id=survey_id).all()
    errors = []

    # Determine which questions are "active" (not conditional, or condition met)
    form_data = request.form

    def is_active_question(q):
        if q.parent_question_id is None:
            return True
        # Check if parent's answer matches trigger
        parent = Question.query.get(q.parent_question_id)
        if parent is None:
            return False
        trigger = q.parent_trigger_value
        if parent.question_type in ("single", "multiple"):
            selected = form_data.getlist(f"q_{parent.id}")
            # trigger can be option id or option text
            for opt in parent.options:
                if str(opt.id) in selected or opt.text in selected:
                    if str(opt.id) == trigger or opt.text == trigger:
                        return True
            return False
        else:
            answer_val = form_data.get(f"q_{parent.id}", "")
            return answer_val == trigger

    active_questions = [q for q in all_questions if is_active_question(q)]

    for q in active_questions:
        if not q.required:
            continue
        if q.question_type in ("single", "multiple"):
            vals = form_data.getlist(f"q_{q.id}")
            if not vals:
                errors.append(f'La pregunta "{q.text[:60]}" es obligatoria.')
        else:
            val = form_data.get(f"q_{q.id}", "").strip()
            if not val:
                errors.append(f'La pregunta "{q.text[:60]}" es obligatoria.')

    if errors:
        questions = (
            Question.query.filter_by(survey_id=survey_id, parent_question_id=None)
            .order_by(Question.order)
            .all()
        )
        return render_template(
            "survey/take.html",
            survey=survey,
            questions=questions,
            user=user,
            errors=errors,
            form_data=form_data,
        )

    # Save response
    response = Response(user_id=user.id, survey_id=survey_id, is_complete=True)
    db.session.add(response)
    db.session.flush()

    for q in active_questions:
        answer = Answer(response_id=response.id, question_id=q.id)
        if q.question_type in ("single", "multiple"):
            selected_ids = form_data.getlist(f"q_{q.id}")
            answer.option_ids = ",".join(selected_ids)
        else:
            answer.text_value = form_data.get(f"q_{q.id}", "").strip()
        db.session.add(answer)

    db.session.commit()
    flash("¡Gracias! Tu respuesta fue registrada.", "success")
    return redirect(url_for("survey.thank_you", survey_id=survey_id))


@survey_bp.route("/<int:survey_id>/terminos/aceptar", methods=["POST"])
@login_required
def terms_accept(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if request.form.get("accept_terms") == "1":
        session[f"tc_accepted_{survey_id}"] = True
        return redirect(url_for("survey.take", survey_id=survey_id))
    flash("Debés aceptar los términos y condiciones para continuar.", "warning")
    return redirect(url_for("survey.terms", survey_id=survey_id))


@survey_bp.route("/<int:survey_id>/gracias")
@login_required
def thank_you(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    session.pop(f"tc_accepted_{survey_id}", None)  # limpiar flag de sesión
    return render_template("survey/thank_you.html", survey=survey)
