from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    grupo_primario = db.Column(db.String(200))
    parcela = db.Column(db.String(100))
    app_access = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responses = db.relationship("Response", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Survey(db.Model):
    __tablename__ = "surveys"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    terms_text = db.Column(db.Text, nullable=True)   # Términos y condiciones (opcional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship(
        "Question", backref="survey", lazy=True, order_by="Question.order"
    )
    responses = db.relationship("Response", backref="survey", lazy=True)

    @property
    def is_open(self):
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(
        db.String(20), nullable=False
    )  # single, multiple, rating, text
    order = db.Column(db.Integer, default=0)
    required = db.Column(db.Boolean, default=True)
    rating_min = db.Column(db.Integer, default=1)
    rating_max = db.Column(db.Integer, default=5)
    # Conditional: this question is shown only when parent_question_id has parent_trigger_value
    parent_question_id = db.Column(
        db.Integer, db.ForeignKey("questions.id"), nullable=True
    )
    parent_trigger_value = db.Column(
        db.String(500), nullable=True
    )  # option id or text value that triggers this subquestion

    options = db.relationship(
        "QuestionOption",
        backref="question",
        lazy=True,
        order_by="QuestionOption.order",
        foreign_keys="QuestionOption.question_id",
    )
    subquestions = db.relationship(
        "Question",
        backref=db.backref("parent", remote_side="Question.id"),
        lazy=True,
        foreign_keys="Question.parent_question_id",
    )
    answers = db.relationship("Answer", backref="question", lazy=True)


class QuestionOption(db.Model):
    __tablename__ = "question_options"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    # If this option is selected, it can trigger subquestions


class Response(db.Model):
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_complete = db.Column(db.Boolean, default=True)

    answers = db.relationship("Answer", backref="response", lazy=True)


class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("responses.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    text_value = db.Column(db.Text)  # for text/rating answers
    # For single/multiple choice, store option ids as comma-separated
    option_ids = db.Column(db.Text)

    def get_option_ids(self):
        if not self.option_ids:
            return []
        return [int(x) for x in self.option_ids.split(",") if x.strip()]
