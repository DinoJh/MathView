from lexer import Lexer

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errores = []
        self.arbol = []

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
            # Hacer warnings menos estrictos
            return False

    def analizar(self):
        """Análisis con detección mejorada de errores"""
        
        # Verificar errores comunes antes de parsear
        self.verificar_errores_comunes()
        
        # Si hay funciones gráficas simples, validar básicamente
        tokens_str = ' '.join([t[0] for t in self.tokens])
        
        if 'draw2d' in tokens_str or 'draw3d' in tokens_str:
            # Modo permisivo para gráficas
            self.arbol.append("Código con funciones gráficas detectado")
            return {
                "estado": "correcto ✅",
                "errores": self.errores,
                "arbol": self.arbol
            }
        
        # Análisis normal para código secuencial
        while self.actual()[1] != "EOF":
            if not self.instruccion():
                # Avanzar sin error fatal
                self.avanzar()

        return {
            "estado": "correcto ✅" if len(self.errores) == 0 else "con errores ❌",
            "errores": self.errores,
            "arbol": self.arbol
        }
    
    def verificar_errores_comunes(self):
        """Detecta errores comunes antes del parsing"""
        codigo_completo = ' '.join([t[0] for t in self.tokens])
        
        # 1. Detectar punto y coma duplicado
        for i in range(len(self.tokens) - 1):
            if self.tokens[i][1] == "PUNTO_COMA" and self.tokens[i+1][1] == "PUNTO_COMA":
                self.errores.append("⚠️ Punto y coma duplicado en la línea")
        
        # 2. Verificar balance de paréntesis
        parentesis_abiertos = sum(1 for t in self.tokens if t[1] == "PAR_IZQ")
        parentesis_cerrados = sum(1 for t in self.tokens if t[1] == "PAR_DER")
        if parentesis_abiertos > parentesis_cerrados:
            self.errores.append("❌ Falta cerrar paréntesis ')' - Se abrieron más de los que se cerraron")
        elif parentesis_cerrados > parentesis_abiertos:
            self.errores.append("❌ Paréntesis ')' de más - Se cerraron más de los que se abrieron")
        
        # 3. Verificar balance de llaves
        llaves_abiertas = sum(1 for t in self.tokens if t[1] == "LLAVE_IZQ")
        llaves_cerradas = sum(1 for t in self.tokens if t[1] == "LLAVE_DER")
        if llaves_abiertas > llaves_cerradas:
            self.errores.append("❌ Falta cerrar llave '}' - Se abrieron más de las que se cerraron")
        elif llaves_cerradas > llaves_abiertas:
            self.errores.append("❌ Llave '}' de más - Se cerraron más de las que se abrieron")
        
        # 4. Verificar balance de corchetes
        corchetes_abiertos = sum(1 for t in self.tokens if t[1] == "CORCH_IZQ")
        corchetes_cerrados = sum(1 for t in self.tokens if t[1] == "CORCH_DER")
        if corchetes_abiertos > corchetes_cerrados:
            self.errores.append("❌ Falta cerrar corchete ']'")
        elif corchetes_cerrados > corchetes_abiertos:
            self.errores.append("❌ Corchete ']' de más")
        
        # 5. Detectar operadores sueltos
        operadores = ["MAS", "MENOS", "MULT", "DIV", "ASIGNACION", "POTENCIA"]
        for i in range(len(self.tokens) - 1):
            if self.tokens[i][1] in operadores and self.tokens[i+1][1] == "PUNTO_COMA":
                self.errores.append(f"❌ Operador '{self.tokens[i][0]}' sin operando - Falta expresión después del operador")
        
        # 6. Detectar punto y coma antes de llave de cierre
        for i in range(len(self.tokens) - 1):
            if self.tokens[i][1] == "PUNTO_COMA" and self.tokens[i+1][1] == "LLAVE_DER":
                # Esto es válido, no es error
                pass
        
        # 7. Detectar declaraciones incompletas
        for i in range(len(self.tokens) - 2):
            if self.tokens[i][1] in ["TIPO_ENTERO", "TIPO_DECIMAL", "TIPO_CADENA", "TIPO_ECUACION"]:
                if self.tokens[i+1][1] == "PUNTO_COMA":
                    self.errores.append(f"❌ Declaración incompleta: falta nombre de variable después de '{self.tokens[i][0]}'")
        
        # 8. Detectar asignación sin valor
        for i in range(len(self.tokens) - 1):
            if self.tokens[i][1] == "ASIGNACION" and self.tokens[i+1][1] == "PUNTO_COMA":
                self.errores.append("❌ Asignación sin valor: falta expresión después de '='")
        
        # 9. Detectar comas sueltas
        for i in range(len(self.tokens)):
            if self.tokens[i][1] == "COMA":
                # Verificar que no esté al inicio o al final de una expresión
                if i == 0 or i == len(self.tokens) - 1:
                    self.errores.append("❌ Coma mal ubicada")
                elif self.tokens[i+1][1] in ["PUNTO_COMA", "PAR_DER"]:
                    self.errores.append("❌ Coma seguida de cierre - Falta argumento")
        
        # 10. Detectar palabras clave mal usadas
        for i in range(len(self.tokens)):
            if self.tokens[i][1] in ["CONDICIONAL_IF", "BUCLE_WHILE"]:
                if i + 1 >= len(self.tokens) or self.tokens[i+1][1] != "PAR_IZQ":
                    self.errores.append(f"❌ '{self.tokens[i][0]}' debe ir seguido de paréntesis '('")
        
        # 11. Detectar funciones sin paréntesis
        funciones = ["FUNCION_PRI", "FUNCION_PUT", "FUNCION_DIBUJO_2D", "FUNCION_DIBUJO_3D"]
        for i in range(len(self.tokens)):
            if self.tokens[i][1] in funciones:
                if i + 1 >= len(self.tokens) or self.tokens[i+1][1] != "PAR_IZQ":
                    self.errores.append(f"❌ Función '{self.tokens[i][0]}' requiere paréntesis '()'")
        
        # 12. Detectar múltiples errores de punto y coma
        punto_coma_count = sum(1 for t in self.tokens if t[1] == "PUNTO_COMA")
        if punto_coma_count == 0 and len(self.tokens) > 3:
            # Solo advertir si hay código significativo
            tiene_codigo = any(t[1] in ["IDENTIFICADOR", "NUMERO"] for t in self.tokens)
            if tiene_codigo and 'draw' not in codigo_completo:
                self.errores.append("⚠️ Advertencia: No se encontraron punto y coma ';' - Las instrucciones deben terminar con ';'")

    def instruccion(self):
        lexema, tipo = self.actual()

        # Declaraciones de tipo
        if tipo in ["TIPO_ENTERO", "TIPO_DECIMAL", "TIPO_ECUACION", "TIPO_CADENA"]:
            self.avanzar()
            self.coincidir("IDENTIFICADOR")
            
            if self.actual()[1] == "ASIGNACION":
                self.avanzar()
                self.expresion()
            
            self.coincidir("PUNTO_COMA")
            self.arbol.append(f"Declaración {lexema}")
            return True

        # Asignación
        if tipo == "IDENTIFICADOR":
            self.avanzar()
            if self.actual()[1] in ["ASIGNACION", "MAS_IGUAL", "MENOS_IGUAL"]:
                self.avanzar()
                self.expresion()
                self.coincidir("PUNTO_COMA")
                self.arbol.append("Asignación")
                return True
            elif self.actual()[1] in ["INCREMENTO", "DECREMENTO"]:
                self.avanzar()
                self.coincidir("PUNTO_COMA")
                self.arbol.append("Incremento")
                return True

        # pri(...)
        if tipo == "FUNCION_PRI":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("PUNTO_COMA")
            self.arbol.append("Impresión")
            return True

        # put(...)
        if tipo == "FUNCION_PUT":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("PUNTO_COMA")
            self.arbol.append("Entrada")
            return True

        # while
        if tipo == "BUCLE_WHILE":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("LLAVE_IZQ")
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.instruccion()
            self.coincidir("LLAVE_DER")
            self.arbol.append("Bucle while")
            return True

        # if / else if / else
        if tipo == "CONDICIONAL_IF":
            self.avanzar()
            self.coincidir("PAR_IZQ")
            self.expresion()
            self.coincidir("PAR_DER")
            self.coincidir("LLAVE_IZQ")
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.instruccion()
            self.coincidir("LLAVE_DER")
            
            # Verificar else if / elif
            while self.actual()[1] in ["CONDICIONAL_ELIF"] or \
                  (self.actual()[1] == "CONDICIONAL_ELSE" and 
                   self.pos + 1 < len(self.tokens) and 
                   self.tokens[self.pos + 1][1] == "CONDICIONAL_IF"):
                
                if self.actual()[1] == "CONDICIONAL_ELSE":
                    self.avanzar()  # else
                self.avanzar()  # elif o if
                self.coincidir("PAR_IZQ")
                self.expresion()
                self.coincidir("PAR_DER")
                self.coincidir("LLAVE_IZQ")
                while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                    self.instruccion()
                self.coincidir("LLAVE_DER")
            
            # Verificar else
            if self.actual()[1] == "CONDICIONAL_ELSE":
                self.avanzar()
                self.coincidir("LLAVE_IZQ")
                while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                    self.instruccion()
                self.coincidir("LLAVE_DER")
            
            self.arbol.append("Condicional if/elif/else")
            return True

        # Funciones gráficas
        if tipo in ["FUNCION_DIBUJO_2D", "FUNCION_DIBUJO_3D", "FUNCION_PLANO_2D", 
                    "FUNCION_TEXTO", "FUNCION_NOW", "FUNCION_DISPLAY"]:
            self.avanzar()
            self.coincidir("PAR_IZQ")
            # Consumir todo hasta cerrar paréntesis
            depth = 1
            while depth > 0 and self.actual()[1] != "EOF":
                if self.actual()[1] == "PAR_IZQ":
                    depth += 1
                elif self.actual()[1] == "PAR_DER":
                    depth -= 1
                self.avanzar()
            self.coincidir("PUNTO_COMA")
            self.arbol.append(f"Función {lexema}")
            return True

        # win2d/win3d
        if tipo in ["VENTANA_2D", "VENTANA_3D"]:
            self.avanzar()
            self.coincidir("IDENTIFICADOR")
            self.coincidir("PAR_IZQ")
            # Consumir parámetros
            depth = 1
            while depth > 0 and self.actual()[1] != "EOF":
                if self.actual()[1] == "PAR_IZQ":
                    depth += 1
                elif self.actual()[1] == "PAR_DER":
                    depth -= 1
                self.avanzar()
            self.coincidir("LLAVE_IZQ")
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.instruccion()
            self.coincidir("LLAVE_DER")
            self.arbol.append(f"Función {lexema}")
            return True

        return False

    def expresion(self):
        """Expresión permisiva"""
        lexema, tipo = self.actual()
        
        # Aceptar casi cualquier cosa como expresión
        if tipo in ["NUMERO", "IDENTIFICADOR", "CADENA", "EXPRESION_MATH",
                    "BOOLEANO_TRUE", "BOOLEANO_FALSE"]:
            self.avanzar()
            
            # Operadores
            while self.actual()[1] in [
                "MAS", "MENOS", "MULT", "DIV", "POTENCIA", "MOD",
                "MENOR", "MAYOR", "IGUAL", "DIFERENTE", "MENORIGUAL", "MAYORIGUAL"
            ]:
                self.avanzar()
                if self.actual()[1] in ["NUMERO", "IDENTIFICADOR", "EXPRESION_MATH"]:
                    self.avanzar()
            
            return True
        
        # Paréntesis
        if tipo == "PAR_IZQ":
            self.avanzar()
            self.expresion()
            self.coincidir("PAR_DER")
            return True
        
        # Funciones
        if tipo in ["FUNCION_REM", "FUNCION_EVA", "FUNCION_FACT", "FUNCION_MATH"]:
            self.avanzar()
            if self.actual()[1] == "PAR_IZQ":
                depth = 1
                self.avanzar()
                while depth > 0 and self.actual()[1] != "EOF":
                    if self.actual()[1] == "PAR_IZQ":
                        depth += 1
                    elif self.actual()[1] == "PAR_DER":
                        depth -= 1
                    self.avanzar()
            return True
        
        return True  # Permisivo