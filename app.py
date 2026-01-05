from flask import Flask, render_template, request, jsonify
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
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
        user_inputs = data.get("inputs", [])

        if not isinstance(codigo, str) or not codigo.strip():
            return jsonify({
                "estado": "error",
                "mensaje": "Código no válido o vacío."
            }), 400

        # ========== FASE 1: ANÁLISIS LÉXICO ==========
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

        # ========== FASE 2: ANÁLISIS SINTÁCTICO ==========
        parser = Parser(tokens)
        resultado_sintactico = parser.analizar()

        if resultado_sintactico["errores"]:
            return jsonify({
                "estado": "error_sintactico",
                "mensaje": "Errores sintácticos encontrados",
                "errores": resultado_sintactico["errores"],
                "tokens": [(t[0], t[1]) for t in tokens]
            })

        # ========== FASE 3: ANÁLISIS SEMÁNTICO ==========
        semantic_analyzer = SemanticAnalyzer(tokens)
        resultado_semantico = semantic_analyzer.analizar()
        
        errores_semanticos = resultado_semantico["errores"]
        advertencias_semanticas = resultado_semantico["advertencias"]
        
        # Si hay errores semánticos, reportarlos antes de ejecutar
        if errores_semanticos:
            return jsonify({
                "estado": "error_semantico",
                "mensaje": "Errores semánticos encontrados",
                "errores": errores_semanticos,
                "advertencias": advertencias_semanticas,
                "tokens": [(t[0], t[1]) for t in tokens],
                "tabla_simbolos": resultado_semantico.get("tabla_simbolos", {})
            })

        # ========== FASE 4: INTERPRETACIÓN Y EJECUCIÓN ==========
        interpreter = Interpreter(codigo, user_inputs)
        resultado_interprete = interpreter.ejecutar()

        # Si hay solicitudes de input, devolver para que el frontend las maneje
        if resultado_interprete.get("solicitudes_input"):
            return jsonify({
                "estado": "necesita_input",
                "mensaje": "El programa requiere entrada del usuario",
                "solicitudes": resultado_interprete["solicitudes_input"]
            })

        # ========== RESULTADO FINAL ==========
        tiene_errores_ejecucion = bool(resultado_interprete.get("errores"))
        
        # Combinar advertencias semánticas con errores de ejecución si los hay
        todos_errores = []
        if advertencias_semanticas:
            todos_errores.extend(advertencias_semanticas)
        if tiene_errores_ejecucion:
            todos_errores.extend(resultado_interprete.get("errores", []))

        return jsonify({
            "estado": "correcto" if not todos_errores else "con_errores",
            "tokens": [(t[0], t[1]) for t in tokens],
            "salida": resultado_interprete.get("texto", ""),
            "debug": resultado_interprete.get("debug", ""),
            "errores": todos_errores,
            "imagen": resultado_interprete.get("imagen", None),
            "acciones": resultado_interprete.get("acciones", []),
            "tabla_simbolos": resultado_semantico.get("tabla_simbolos", {})
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
