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
            "put": "FUNCION_PUT",
            "pri": "FUNCION_PRI",
            "eva": "FUNCION_EVA",
            "rem": "FUNCION_REM",
            "fact": "FUNCION_FACT",
            # Funciones matemáticas
            "sin": "FUNCION_MATH",
            "cos": "FUNCION_MATH",
            "tan": "FUNCION_MATH",
            "exp": "FUNCION_MATH",
            "log": "FUNCION_MATH",
            "ln": "FUNCION_MATH",
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
            '**': 'POTENCIA',
            '`': 'BACKTICK',
            '++': 'INCREMENTO',
            '--': 'DECREMENTO',
            '+=': 'MAS_IGUAL',
            '-=': 'MENOS_IGUAL'
        }

    def tokenizar(self, codigo_fuente):
        tokens = []
        errores = []

        # Eliminar comentarios
        codigo_fuente = re.sub(r'//.*', '', codigo_fuente)
        codigo_fuente = re.sub(r'/\*.*?\*/', '', codigo_fuente, flags=re.S)

        # Patrón mejorado que captura:
        # - Expresiones entre //...//
        # - Números negativos: -123, -45.67
        # - Operadores dobles: ==, !=, <=, >=, **, ++, --, +=, -=
        # - Palabras: identificadores y palabras clave
        # - Cadenas entre comillas
        # - Símbolos individuales incluyendo `
        patron = r'(//[^/]+//|\'[^\']*\'|"[^"]*"|-?\d+\.?\d*|==|!=|<=|>=|\*\*|\+\+|--|\+=|-=|\b\w+\b|[+\-*/%=;:(),{}\[\]<>^`])'
        
        partes = re.findall(patron, codigo_fuente)

        for lexema in partes:
            lexema_stripped = lexema.strip()
            if not lexema_stripped:
                continue

            # Expresiones matemáticas entre //...//
            if lexema_stripped.startswith('//') and lexema_stripped.endswith('//'):
                tokens.append((lexema_stripped, "EXPRESION_MATH"))
                continue

            # Cadenas entre comillas
            if (lexema_stripped.startswith('"') and lexema_stripped.endswith('"')) or \
               (lexema_stripped.startswith("'") and lexema_stripped.endswith("'")):
                tokens.append((lexema_stripped, "CADENA"))
                continue

            # Palabra clave (case-insensitive para funciones)
            lexema_lower = lexema_stripped.lower()
            if lexema_lower in self.PALABRAS_CLAVE:
                tokens.append((lexema_stripped, self.PALABRAS_CLAVE[lexema_lower]))
                continue

            # Operadores de dos caracteres
            if lexema_stripped in ['==', '!=', '<=', '>=', '**', '++', '--', '+=', '-=']:
                tokens.append((lexema_stripped, self.SIMBOLOS[lexema_stripped]))
                continue

            # Símbolos de un carácter
            if lexema_stripped in self.SIMBOLOS:
                tokens.append((lexema_stripped, self.SIMBOLOS[lexema_stripped]))
                continue

            # Números (incluyendo negativos y decimales)
            if re.match(r'^-?\d+\.?\d*$', lexema_stripped):
                tokens.append((lexema_stripped, "NUMERO"))
                continue

            # Identificadores
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', lexema_stripped):
                tokens.append((lexema_stripped, "IDENTIFICADOR"))
                continue

            # Si no coincide con nada, es desconocido
            errores.append(f"Token desconocido: '{lexema_stripped}'")
            tokens.append((lexema_stripped, "DESCONOCIDO"))

        return {
            "tokens": tokens,
            "errores": errores
        }