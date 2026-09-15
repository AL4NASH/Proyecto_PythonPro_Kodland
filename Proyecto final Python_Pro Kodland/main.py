from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///huella.db'
app.config["SECRET_KEY"] = "una-clave-secreta-larga"
db = SQLAlchemy()
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


@app.route("/")
def inicio():
    return render_template("bienvenida.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        password_confirmacion = request.form["password_confirmacion"]

        # Verificar si las contraseñas coinciden
        if password != password_confirmacion:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for("registro"))

        # Verificar si el correo ya está registrado
        if Usuario.query.filter_by(email=email).first():
            flash("El correo electrónico ya está registrado.")
            return redirect(url_for("registro"))

        # Crear nuevo usuario
        nuevo_usuario = Usuario(nombre=nombre, email=email)
        nuevo_usuario.password_hash = generate_password_hash(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Cuenta creada exitosamente.")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/cuestionario", methods=["GET", "POST"])
@login_required
def cuestionario():

    if request.method == "POST":

        print(request.form)

        transporte = request.form.get("transporte")
        kilometros = request.form.get("kilometros")
        energia = request.form.get("energia")
        ducha = request.form.get("ducha")

        if not transporte or not kilometros or not energia or not ducha:
            flash("Debes responder todas las preguntas.")
            return redirect(url_for("cuestionario"))

        kilometros = int(kilometros)
        energia = int(energia)
        ducha = int(ducha)

        puntos_transporte = {
            "carro": 2,
            "moto": 4,
            "bus": 6,
            "bicicleta": 10,
            "caminando": 10
        }

        puntuacion_transporte = puntos_transporte[transporte]

        if transporte == "bicicleta" or transporte == "caminando":
            valores = [puntuacion_transporte, energia, ducha]
        else:
            valores = [puntuacion_transporte, kilometros, energia, ducha]

        promedio = round(sum(valores) / len(valores), 1)

        resultado_anterior = Resultado.query.filter_by(
            usuario_id=current_user.id
        ).order_by(Resultado.id.desc()).first()

        if resultado_anterior is None:
            comparacion = "Esta es tu primera medición. Este resultado servirá como punto de referencia."

        elif promedio > resultado_anterior.promedio:
            comparacion = "¡Felicidades! Mejoraste respecto a tu resultado anterior."

        elif promedio < resultado_anterior.promedio:
            comparacion = "Tu resultado disminuyó respecto a tu medición anterior."

        else:
            comparacion = "Tu resultado se mantuvo igual que en tu medición anterior."

        if promedio >= 8:
            resultado = "¡Felicidades! Tus hábitos son favorables para reducir tu huella de carbono."

        elif promedio >= 5:
            resultado = "Vas bien, aunque todavía puedes mejorar algunos hábitos."

        else:
            resultado = "Por mejorar. Puedes realizar varios cambios para reducir tu huella de carbono."

        if transporte == "carro" or transporte == "moto":
            consejo_transporte = "Considera utilizar más el transporte público, caminar o usar bicicleta cuando sea posible."

        elif transporte == "bicicleta" or transporte == "caminando":
            consejo_transporte = "¡Excelente! Este medio de transporte tiene un impacto ambiental muy bajo."

        else:
            consejo_transporte = "El transporte público ayuda a reducir las emisiones por persona."

        if energia < 6:
            consejo_energia = "Intenta reducir tu consumo de energía en casa, por ejemplo, apagando luces y electrodomésticos cuando no los uses."
        else:
            consejo_energia = "¡Bien hecho! Mantener un consumo de energía bajo ayuda a reducir tu huella de carbono."

        if ducha == 10:
            consejo_agua = "¡Muy bien! Tus duchas cortas ayudan a ahorrar agua."

        elif ducha == 5:
            consejo_agua = "Tu consumo de agua es moderado. Intenta reducir un poco la duración de tus duchas."

        else:
            consejo_agua = "Tus duchas son largas. Reducir su duración puede ayudar significativamente a disminuir el consumo de agua."

        nuevo_resultado = Resultado(
            usuario_id=current_user.id,
            transporte=transporte,
            kilometros=kilometros,
            energia=energia,
            ducha=ducha,
            promedio=promedio
        )

        db.session.add(nuevo_resultado)
        db.session.commit()
        
        return render_template(
            "index.html",
            promedio=round(promedio, 1),
            resultado=resultado,
            consejo_transporte=consejo_transporte,
            consejo_energia=consejo_energia,
            comparacion=comparacion,
            consejo_agua=consejo_agua
        )

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(email=email).first()

        print("Email recibido:", email)
        print("¿Usuario encontrado?:", usuario is not None)

        if usuario:
            print("¿Contraseña correcta?:",
                  check_password_hash(usuario.password_hash, password))

        if usuario and check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            return redirect(url_for("cuestionario"))
        else:
            flash("Correo electrónico o contraseña incorrectos.")
            return redirect(url_for("login"))

    return render_template("login.html")


class Resultado(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=False
    )

    transporte = db.Column(db.String(30), nullable=False)
    kilometros = db.Column(db.Integer, nullable=False)
    energia = db.Column(db.Integer, nullable=False)
    ducha = db.Column(db.Integer, nullable=False)

    promedio = db.Column(db.Float, nullable=False)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
