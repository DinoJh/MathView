# ============================================
#  ANALIZADOR SINTACTICO - Proyecto Compilador Web
#  Autor: Dino & ChatGPT
#  Integrado con lexer.py
# ============================================

from lexer import Lexer

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errores = []
        self.arbol = []  # Representacion simplificada del AST

    # -------------------------
    #  Funciones basicas
    # -------------------------
    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "EOF")

    def avanzar(self):
        self.pos += 1

    def coincidir(self, tipo_esperado):
        lexema, tipo = self.actual()
        if tipo == tipo_esperado:
            self.avanzar()
            return True
        else:
            self.errores.append(
                f"Error de sintaxis: se esperaba '{tipo_esperado}' pero se encontro '{lexema}' ({tipo})"
            )
            return False

    # -------------------------
    #  Analizador principal
    # -------------------------
    def analizar(self):
        while self.actual()[1] != "EOF":
            if not self.instruccion():
                # Si algo falla, avanzamos para evitar bucles infinitos
                self.avanzar()

        return {
            "estado": "correcto ✅" if not self.errores else "errores ❌",
            "errores": self.errores,
            "arbol": self.arbol
        }

    # -------------------------
    #  Reglas sintacticas
    # -------------------------
    def instruccion(self):
        lexema, tipo = self.actual()

        # win2d ventana;
        if tipo in ["VENTANA_2D", "VENTANA_3D"]:
            self.avanzar()
            if not self.coincidir("IDENTIFICADOR"): return False
            self.coincidir("PUNTO_COMA")
            self.arbol.append(f"Declaracion de ventana: {lexema}")
            return True

        # var x = 5;
        if tipo == "VAR":
            self.avanzar()
            if not self.coincidir("IDENTIFICADOR"): return False
            self.coincidir("ASIGNACION")
            self.expresion()
            self.coincidir("PUNTO_COMA")
            self.arbol.append("Declaracion de variable")
            return True

        # draw2d(x^2, -5, 5);
        if tipo in ["FUNCION_DIBUJO_2D", "FUNCION_DIBUJO_3D"]:
            funcion = lexema
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            while self.actual()[1] == "COMA":
                self.avanzar()
                self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("PUNTO_COMA")
            self.arbol.append(f"Llamada a {funcion}")
            return True

        # if (condicion) { ... }
        if tipo == "CONDICIONAL_IF":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("LLAVE_IZQ")
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.instruccion()
            self.coincidir("LLAVE_DER")
            self.arbol.append("Bloque IF")
            return True

        # while (condicion) { ... }
        if tipo == "BUCLE_WHILE":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("LLAVE_IZQ")
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.instruccion()
            self.coincidir("LLAVE_DER")
            self.arbol.append("Bucle WHILE")
            return True

        # Si no se reconoce
        self.errores.append(f"Instruccion desconocida o invalida cerca de '{lexema}'")
        return False

    # -------------------------
    #  Expresiones basicas
    # -------------------------
    def expresion(self):
        lexema, tipo = self.actual()
        if tipo in ["NUMERO", "IDENTIFICADOR"]:
            self.avanzar()
            while self.actual()[1] in [
                "MAS", "MENOS", "MULT", "DIV",
                "MENOR", "MAYOR", "IGUAL", "DIFERENTE",
                "MENORIGUAL", "MAYORIGUAL"
            ]:
                self.avanzar()
                if self.actual()[1] in ["NUMERO", "IDENTIFICADOR"]:
                    self.avanzar()
                else:
                    self.errores.append(f"Error: operando esperado despues de '{lexema}'")
                    return False
            return True
        else:
            self.errores.append(f"Error: expresion invalida cerca de '{lexema}'")
            return False
