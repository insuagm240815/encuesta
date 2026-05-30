from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, User
from .factory import limiter

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 30 per hour")
def login():
    if request.method == "POST":
        documento = request.form.get("documento", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(documento=documento).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            session["is_operator"] = user.is_operator
            session["user_name"] = user.nombre
            if user.is_admin or user.is_operator:
                if user.must_change_password and not user.is_admin:
                    return redirect(url_for("auth.change_password"))
                return redirect(url_for("admin.index"))
            # Si debe cambiar contraseña, redirigir antes de continuar
            if user.must_change_password:
                return redirect(url_for("auth.change_password"))
            return redirect(url_for("survey.index"))
        flash("UF o contraseña incorrectos.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/cambiar-contrasena", methods=["GET", "POST"])
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


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
