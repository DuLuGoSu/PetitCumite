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

    usuario = session['usuario']
    eventos = obtener_eventos()   
    eventos_confirmados = obtener_eventos_confirmados(usuario)

    # Obtener usuarios confirmados para cada evento
    usuarios_confirmados = {}
    for evento in eventos:
        usuarios_confirmados[evento[0]] = obtener_usuarios_confirmados(evento[0])

    return render_template("calendario.html", eventos=eventos, eventos_confirmados=eventos_confirmados, usuarios_confirmados=usuarios_confirmados)

def obtener_usuarios_confirmados(id_evento):
    cursor = db.cursor()
    consulta = """
        SELECT u.nombre_usuario
        FROM asistencias a
        JOIN usuarios u ON a.id_usuario = u.id
        WHERE a.id_evento = %s
    """
    valores = (id_evento,)
    cursor.execute(consulta, valores)
    usuarios_confirmados = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return usuarios_confirmados


def obtener_eventos():
    cursor = db.cursor()
    consulta = "SELECT * FROM eventos"
    cursor.execute(consulta)
    eventos = cursor.fetchall()
    cursor.close()
    return eventos

def obtener_eventos_confirmados(usuario):
    cursor = db.cursor()
    consulta = "SELECT id_evento FROM asistencias WHERE id_usuario = %s"
    valores = (usuario,)
    cursor.execute(consulta, valores)
    eventos_confirmados = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return eventos_confirmados
    
@app.route("/guardar_evento", methods=["POST"])
def guardar_evento():
    if 'usuario' not in session:
        return redirect(url_for("login"))

    datos = request.form
    cursor = db.cursor()
    consulta = "INSERT INTO eventos (titulo, descripcion, fecha, color) VALUES (%s, %s, %s, %s)"
    valores = (datos["titulo"], datos["descripcion"], datos["fecha"],datos["color"])
    cursor.execute(consulta, valores)
    db.commit()
    cursor.close()
    
    return redirect(url_for("calendario"))

@app.route("/confirmar_asistencia/<int:id_evento>", methods=["GET", "POST"])
def confirmar_asistencia(id_evento):
    if 'usuario' not in session:
        return redirect(url_for("login"))

    id_usuario = session.get("usuario")
    
    cursor = db.cursor()
    consulta = "INSERT INTO asistencias (id_evento, id_usuario) VALUES (%s, %s)"
    valores = (id_evento, id_usuario)
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
