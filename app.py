from flask import Flask, render_template, request, jsonify
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
import traceback

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compilar", methods=["POST"])
def compilar():
    try:
        codigo = request.json.get("codigo", "") if request.is_json else request.form.get("codigo", "")

        if not isinstance(codigo, str) or not codigo.strip():
            return jsonify({
                "estado": "error",
                "mensaje": "Código no válido o vacío."
            }), 400

        # 1. ANÁLISIS LÉXICO
        lexer = Lexer()
        resultado_lexico = lexer.tokenizar(codigo)
        tokens = resultado_lexico["tokens"]
        errores_lexico = resultado_lexico["errores"]

        if errores_lexico:
            return jsonify({
                "estado": "error_lexico",
                "errores": errores_lexico,
                "tokens": [(t[0], t[1]) for t in tokens]
            })

        # 2. ANÁLISIS SINTÁCTICO
        parser = Parser(tokens)
        resultado_sintactico = parser.analizar()

        if resultado_sintactico["errores"]:
            return jsonify({
                "estado": "error_sintactico",
                "errores": resultado_sintactico["errores"],
                "tokens": [(t[0], t[1]) for t in tokens]
            })

        # 3. INTERPRETACIÓN
        interpreter = Interpreter(codigo)
        resultado_interprete = interpreter.ejecutar()

        return jsonify({
            "estado": "correcto",
            "tokens": [(t[0], t[1]) for t in tokens],
            "texto": resultado_interprete.get("texto", ""),
            "imagen": resultado_interprete.get("imagen", None),
            "acciones": resultado_interprete.get("acciones", [])
        })

    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": f"Error interno: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)