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
        data = request.get_json()
        codigo = data.get("codigo", "")
        user_inputs = data.get("inputs", [])  # Inputs del usuario

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
                "mensaje": "Errores léxicos encontrados",
                "errores": errores_lexico,
                "tokens": [(t[0], t[1]) for t in tokens]
            })

        # 2. ANÁLISIS SINTÁCTICO
        parser = Parser(tokens)
        resultado_sintactico = parser.analizar()

        if resultado_sintactico["errores"]:
            return jsonify({
                "estado": "error_sintactico",
                "mensaje": "Errores sintácticos encontrados",
                "errores": resultado_sintactico["errores"],
                "tokens": [(t[0], t[1]) for t in tokens]
            })

        # 3. INTERPRETACIÓN
        interpreter = Interpreter(codigo, user_inputs)
        resultado_interprete = interpreter.ejecutar()

        # Si hay solicitudes de input, devolver para que el frontend las maneje
        if resultado_interprete.get("solicitudes_input"):
            return jsonify({
                "estado": "necesita_input",
                "mensaje": "El programa requiere entrada del usuario",
                "solicitudes": resultado_interprete["solicitudes_input"]
            })

        # Compilación exitosa
        return jsonify({
            "estado": "correcto" if not resultado_interprete.get("errores") else "con_errores",
            "tokens": [(t[0], t[1]) for t in tokens],
            "salida": resultado_interprete.get("texto", ""),
            "debug": resultado_interprete.get("debug", ""),
            "errores": resultado_interprete.get("errores", []),
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