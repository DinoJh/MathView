# ============================================
#  SERVIDOR FLASK - Proyecto Compilador Web (ACTUALIZADO)
#  Autor: Dino & ChatGPT
#  Cambios: ahora pasamos el 'codigo' fuente al Interpreter avanzado
# ============================================

from flask import Flask, render_template, request, jsonify
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

app = Flask(__name__)

# Página principal
@app.route("/")
def index():
    return render_template("index.html")


# Endpoint que recibe el código del usuario
@app.route("/compilar", methods=["POST"])
def compilar():
    codigo = request.form.get("codigo", "")

    # Sanitizar mínimo
    if not isinstance(codigo, str):
        return jsonify({"estado": "error", "mensaje": "Código no válido."}), 400

    # 1. ANALISIS LEXICO (opcional para retroalimentación)
    lexer = Lexer()
    resultado_lexico = lexer.tokenizar(codigo)
    tokens = resultado_lexico["tokens"]
    errores_lexico = resultado_lexico["errores"]

    if errores_lexico:
        return jsonify({
            "estado": "error_lexico",
            "errores": errores_lexico,
            "tokens": tokens
        })

    # 2. ANALISIS SINTACTICO (opcional para retroalimentación)
    parser = Parser(tokens)
    resultado_sintactico = parser.analizar()

    if resultado_sintactico["errores"]:
        return jsonify({
            "estado": "error_sintactico",
            "errores": resultado_sintactico["errores"],
            "tokens": tokens
        })

    # 3. INTERPRETACION (AHORA USAMOS EL CÓDIGO FUENTE DIRECTAMENTE)
    # Pasamos 'codigo' al Interpreter avanzado para que extraiga y ejecute
    interpreter = Interpreter(codigo)
    resultado_interprete = interpreter.ejecutar()

    # Devolver todo en JSON
    return jsonify({
        "estado": "correcto",
        "tokens": tokens,
        "texto": resultado_interprete.get("texto", ""),
        "imagen": resultado_interprete.get("imagen", None),
        "acciones": resultado_interprete.get("acciones", [])
    })


# Ejecución local
if __name__ == "__main__":
    # En desarrollo puedes dejar debug=True, pero para deploy en Render pon debug=False
    app.run(debug=True)
