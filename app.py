from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt

app = Flask(__name__)
app.secret_key = 'mysecretkey'

db = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="1234",
    database="calendario"
)

def autenticar_usuario(nombre_usuario, contrasena):
    contrasena = contrasena.encode('utf-8')
    cursor = db.cursor()
    consulta = "SELECT * FROM usuarios WHERE nombre_usuario = %s"
    valores = (nombre_usuario,)
    cursor.execute(consulta, valores)
    usuario = cursor.fetchone()
    cursor.close()
    if usuario and bcrypt.checkpw(contrasena, usuario[2].encode('utf-8')):
        return usuario
    return None

def crear_usuario(nombre_usuario, contrasena):
    contrasena = contrasena.encode('utf-8')
    contrasena_hashed = bcrypt.hashpw(contrasena, bcrypt.gensalt())
    cursor = db.cursor()
    consulta = "INSERT INTO usuarios (nombre_usuario, contrasena) VALUES (%s, %s)"
    valores = (nombre_usuario, contrasena_hashed.decode('utf-8'))
    cursor.execute(consulta, valores)
    db.commit()
    cursor.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calendario")
def calendario():
    if 'usuario' not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()
    consulta = "SELECT * FROM eventos"
    cursor.execute(consulta)
    eventos = cursor.fetchall()
    cursor.close()
    return render_template("calendario.html", eventos=eventos)


@app.route("/guardar_evento", methods=["POST"])
def guardar_evento():
    if 'usuario' not in session:
        return redirect(url_for("login"))

    datos = request.form
    cursor = db.cursor()
    consulta = "INSERT INTO eventos (titulo, descripcion, fecha) VALUES (%s, %s, %s)"
    valores = (datos["titulo"], datos["descripcion"], datos["fecha"])
    cursor.execute(consulta, valores)
    db.commit()
    cursor.close()
    
    return redirect(url_for("calendario"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if 'usuario' in session:
        return redirect(url_for("calendario"))

    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"]
        contrasena = request.form["contrasena"]
        usuario = autenticar_usuario(nombre_usuario, contrasena)
        if usuario:
            session['usuario'] = usuario[0]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", mensaje="Credenciales inválidas")
    else:
        return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if 'usuario' in session:
        return redirect(url_for("calendario"))

    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"]
        contrasena = request.form["contrasena"]
        crear_usuario(nombre_usuario, contrasena)
        return redirect(url_for("login"))
    else:
        return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop('usuario', None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)