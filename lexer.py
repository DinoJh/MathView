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
            "draw3d": "FUNCION_DIBUJO_3D",
            "plane2d": "FUNCION_PLANO_2D",
            "plane3d": "FUNCION_PLANO_3D",
            "vector2d": "FUNCION_VECTOR_2D",
            "vector3d": "FUNCION_VECTOR_3D",
            "text": "FUNCION_TEXTO",
            "now": "FUNCION_NOW",
            "lost": "FUNCION_LOST",
            # Funciones matemáticas
            "sin": "FUNCION_MATH",
            "cos": "FUNCION_MATH",
            "tan": "FUNCION_MATH",
            "exp": "FUNCION_MATH",
            "log": "FUNCION_MATH",
            "sqrt": "FUNCION_MATH",
            "abs": "FUNCION_MATH",
            "arctan2": "FUNCION_MATH",
            "arcsin": "FUNCION_MATH",
            "arccos": "FUNCION_MATH",
            "sinh": "FUNCION_MATH",
            "cosh": "FUNCION_MATH",
            "pi": "CONSTANTE_MATH",
            "e": "CONSTANTE_MATH"
        }

        # Símbolos y operadores
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
            '^': 'POTENCIA',
            '<': 'MENOR',
            '>': 'MAYOR',
            '==': 'IGUAL',
            '!=': 'DIFERENTE',
            '>=': 'MAYORIGUAL',
            '<=': 'MENORIGUAL',
            '**': 'POTENCIA'
        }

    def tokenizar(self, codigo_fuente):
        tokens = []
        errores = []

        # Eliminar comentarios
        codigo_fuente = re.sub(r'//.*', '', codigo_fuente)
        codigo_fuente = re.sub(r'/\*.*?\*/', '', codigo_fuente, flags=re.S)

        # Patrón mejorado que captura:
        # - Números negativos: -123, -45.67
        # - Operadores dobles: ==, !=, <=, >=, **
        # - Palabras: identificadores y palabras clave
        # - Cadenas entre comillas
        # - Símbolos individuales
        patron = r'(-?\d+\.?\d*|==|!=|<=|>=|\*\*|"[^"]*"|\'[^\']*\'|\b\w+\b|[+\-*/%=;:(),{}\[\]<>^])'
        
        partes = re.findall(patron, codigo_fuente)

        for lexema in partes:
            lexema = lexema.strip()
            if not lexema:
                continue

            # Cadenas entre comillas
            if (lexema.startswith('"') and lexema.endswith('"')) or \
               (lexema.startswith("'") and lexema.endswith("'")):
                tokens.append((lexema, "CADENA"))
                continue

            # Palabra clave (case-insensitive para funciones)
            lexema_lower = lexema.lower()
            if lexema_lower in self.PALABRAS_CLAVE:
                tokens.append((lexema, self.PALABRAS_CLAVE[lexema_lower]))
                continue

            # Operadores de dos caracteres
            if lexema in ['==', '!=', '<=', '>=', '**']:
                tokens.append((lexema, self.SIMBOLOS[lexema]))
                continue

            # Símbolos de un carácter
            if lexema in self.SIMBOLOS:
                tokens.append((lexema, self.SIMBOLOS[lexema]))
                continue

            # Números (incluyendo negativos y decimales)
            if re.match(r'^-?\d+\.?\d*$', lexema):
                tokens.append((lexema, "NUMERO"))
                continue

            # Identificadores
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', lexema):
                tokens.append((lexema, "IDENTIFICADOR"))
                continue

            # Si no coincide con nada, es desconocido
            errores.append(f"Token desconocido: '{lexema}'")
            tokens.append((lexema, "DESCONOCIDO"))

        return {
            "tokens": tokens,
            "errores": errores
        }