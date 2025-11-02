# ============================================
#  ANALIZADOR LEXICO - Proyecto Compilador Web
#  Autor: Dino & ChatGPT
#  Adaptado para Flask
# ============================================

import re

class Lexer:
    def __init__(self):
        # Palabras clave del lenguaje
        self.PALABRAS_CLAVE = {
            "var": "VAR",
            "int": "TIPO_ENTERO",
            "dec": "TIPO_DECIMAL",
            "pos": "TIPO_POSITIVO",
            "bin": "TIPO_BINARIO",
            "string": "TIPO_CADENA",
            "chain": "TIPO_CHAIN",
            "ecu": "TIPO_ECUACION",
            "win2d": "VENTANA_2D",
            "win3d": "VENTANA_3D",
            "void": "TIPO_VACIO",

            "true": "BOOLEANO_TRUE",
            "false": "BOOLEANO_FALSE",

            "if": "CONDICIONAL_IF",
            "elif": "CONDICIONAL_ELIF",
            "else": "CONDICIONAL_ELSE",
            "while": "BUCLE_WHILE",
            "return": "RETORNO",
            "display": "FUNCION_DISPLAY",
            "move": "FUNCION_MOVE",
            "config": "FUNCION_CONFIG",
            "draw2d": "FUNCION_DIBUJO_2D",
            "plane2d": "FUNCION_PLANO_2D",
            "plane3d": "FUNCION_PLANO_3D",
            "vector2d": "FUNCION_VECTOR_2D",
            "vector3d": "FUNCION_VECTOR_3D",
            "text": "FUNCION_TEXTO",
            "now": "FUNCION_NOW",
            "lost": "FUNCION_LOST"
        }

        # Simbolos y operadores
        self.SIMBOLOS = {
            '(': 'PAR_IZQ',
            ')': 'PAR_DER',
            '{': 'LLAVE_IZQ',
            '}': 'LLAVE_DER',
            '[': 'CORCH_IZQ',
            ']': 'CORCH_DER',
            ',': 'COMA',
            ';': 'PUNTO_COMA',
            ':': 'DOSPUNTOS',
            '=': 'ASIGNACION',
            '+': 'MAS',
            '-': 'MENOS',
            '*': 'MULT',
            '/': 'DIV',
            '%': 'MOD',
            '<': 'MENOR',
            '>': 'MAYOR',
            '==': 'IGUAL',
            '!=': 'DIFERENTE',
            '>=': 'MAYORIGUAL',
            '<=': 'MENORIGUAL'
        }

        # Expresiones regulares
        self.regex_numero = re.compile(r'^-?\d+(\.\d+)?$')
        self.regex_identificador = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    # -----------------------------------------------------
    # Métodos de ayuda
    # -----------------------------------------------------
    def es_numero(self, lexema):
        return bool(self.regex_numero.match(lexema))

    def es_identificador(self, lexema):
        return bool(self.regex_identificador.match(lexema))

    # -----------------------------------------------------
    # Función principal de tokenización
    # -----------------------------------------------------
    def tokenizar(self, codigo_fuente):
        tokens = []
        errores = []

        # Eliminar comentarios (// y /* */)
        codigo_fuente = re.sub(r'//.*', '', codigo_fuente)
        codigo_fuente = re.sub(r'/\*.*?\*/', '', codigo_fuente, flags=re.S)

        # Separar por espacios, palabras y simbolos
        patron = r'(\b\w+\b|==|!=|<=|>=|[+\-*/%=;:(),{}\[\]<>])'
        partes = re.findall(patron, codigo_fuente)

        for lexema in partes:
            if lexema.strip() == '':
                continue

            # Palabra clave
            if lexema in self.PALABRAS_CLAVE:
                tokens.append((lexema, self.PALABRAS_CLAVE[lexema]))
                continue

            # Símbolo u operador
            if lexema in self.SIMBOLOS:
                tokens.append((lexema, self.SIMBOLOS[lexema]))
                continue

            # Número
            if self.es_numero(lexema):
                tokens.append((lexema, "NUMERO"))
                continue

            # Identificador
            if self.es_identificador(lexema):
                tokens.append((lexema, "IDENTIFICADOR"))
                continue

            # Desconocido
            errores.append(f"Token desconocido: {lexema}")
            tokens.append((lexema, "DESCONOCIDO"))

        return {
            "tokens": tokens,
            "errores": errores
        }
