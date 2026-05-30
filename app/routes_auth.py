from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_
from .models import db, User
from .extensions import limiter

auth_bp = Blueprint("auth", __name__)


def normalizar_uf(uf):
    """Normaliza UF quitando ceros a la izquierda del número base.
    Ejemplos: '0425' -> '425', '00425-INQ' -> '425-INQ', '425' -> '425'
    """
    uf = uf.strip().upper()
    if '-' in uf:
        partes = uf.split('-', 1)
        num = partes[0].lstrip('0') or '0'
        return f"{num}-{partes[1]}"
    else:
        return uf.lstrip('0') or '0'


def buscar_usuario(uf_input):
    """Busca usuario por UF normalizando ceros a la izquierda."""
    uf_norm = normalizar_uf(uf_input)
    # Buscar todas las UFs que podrían coincidir
    users = User.query.filter_by(is_admin=False).all()
    for u in users:
        if normalizar_uf(u.documento) == uf_norm:
            return u
    # También buscar admin por documento exacto
    return User.query.filter_by(documento=uf_input).first()


@auth_bp.route("/acceso", methods=["GET", "POST"])
@limiter.limit("20 per minute; 100 per hour")
def login():
    if request.method == "POST":
        uf_input = request.form.get("documento", "").strip()

        user = buscar_usuario(uf_input)

        # Admin requiere contraseña, usuarios normales solo UF
        if user and user.is_admin:
            password = request.form.get("password", "").strip()
            if not user.check_password(password):
                flash("Credenciales incorrectas.", "error")
                return render_template("auth/login.html", is_admin_attempt=True)
        elif not user:
            flash("UF no encontrada.", "error")
            return render_template("auth/login.html")

        session["user_id"] = user.id
        session["is_admin"] = user.is_admin
        session["is_operator"] = getattr(user, 'is_operator', False)
        session["user_name"] = user.nombre

        if user.is_admin or session["is_operator"]:
            return redirect(url_for("admin.index"))
        return redirect(url_for("survey.index"))

    return render_template("auth/login.html")


@auth_bp.route("/perfil/seguridad", methods=["GET", "POST"])
def change_password():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nueva = request.form.get("nueva", "").strip()
        confirmar = request.form.get("confirmar", "").strip()

        if len(nueva) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
        elif nueva != confirmar:
            flash("Las contraseñas no coinciden.", "error")
        else:
            user.set_password(nueva)
            user.must_change_password = False
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("survey.index"))

    return render_template("auth/change_password.html", user=user)


@auth_bp.route("/salir")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
