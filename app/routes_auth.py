from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        documento = request.form.get("documento", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(documento=documento).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            session["user_name"] = user.nombre
            if user.is_admin:
                return redirect(url_for("admin.index"))
            return redirect(url_for("survey.index"))
        flash("Documento o contraseña incorrectos.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
