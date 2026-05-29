from flask import Flask, redirect, url_for
from .config import get_config
from .models import db, User
from .routes_auth import auth_bp
from .routes_admin import admin_bp
from .routes_survey import survey_bp


def create_app(config_override=None):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    cfg = config_override or get_config()
    app.config.from_object(cfg)

    db.init_app(app)

    # Filtro Jinja2 para convertir Markdown básico a HTML
    import re as _re
    def markdown_to_html(text):
        if not text:
            return ""
        t = text
        t = _re.sub(r'&', '&amp;', t)
        t = _re.sub(r'<', '&lt;', t)
        t = _re.sub(r'>', '&gt;', t)
        t = _re.sub(r'^### (.+)$', r'<h3>\1</h3>', t, flags=_re.MULTILINE)
        t = _re.sub(r'^## (.+)$',  r'<h2>\1</h2>', t, flags=_re.MULTILINE)
        t = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = _re.sub(r'\*(.+?)\*',     r'<em>\1</em>', t)
        t = _re.sub(r'^- (.+)$', r'<li>\1</li>', t, flags=_re.MULTILINE)
        t = _re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', t, flags=_re.DOTALL)
        t = _re.sub(r'^---$', '<hr>', t, flags=_re.MULTILINE)
        t = _re.sub(r'\n{2,}', '</p><p>', t)
        t = _re.sub(r'\n', '<br>', t)
        return f'<p>{t}</p>'
    app.jinja_env.filters['markdown_to_html'] = markdown_to_html

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(survey_bp)

    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            db.session.rollback()
        _seed_admin()

    return app


def _seed_admin():
    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            documento="admin",
            nombre="Administrador",
            email="",
            grupo_primario="Admin",
            is_admin=True,
        )
        admin.set_password("admin1234")
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin creado: documento=admin, contraseña=admin1234")
