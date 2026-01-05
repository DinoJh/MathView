"""
Analizador Semántico para MathView
Detecta errores semánticos según las especificaciones del lenguaje
"""

class SemanticAnalyzer:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errores = []
        self.advertencias = []
        
        # Tabla de símbolos: {nombre: {'tipo': str, 'ambito': int, 'inicializada': bool}}
        self.tabla_simbolos = {}
        self.ambito_actual = 0
        self.pila_ambitos = [{}]  # Stack de ámbitos
        
        # Contexto de ejecución
        self.en_contexto_grafico = False
        self.en_funcion = None  # Guarda info de función actual {'nombre': str, 'tipo_retorno': str}
        
    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "EOF")
    
    def avanzar(self):
        self.pos += 1
    
    def analizar(self):
        """Realiza análisis semántico completo"""
        try:
            while self.actual()[1] != "EOF":
                self.analizar_instruccion()
        except Exception as e:
            self.errores.append(f"Error crítico en análisis semántico: {str(e)}")
        
        return {
            "errores": self.errores,
            "advertencias": self.advertencias,
            "tabla_simbolos": self.tabla_simbolos
        }
    
    def analizar_instruccion(self):
        """Analiza una instrucción"""
        lexema, tipo = self.actual()
        
        # Declaraciones
        if tipo in ["TIPO_ENTERO", "TIPO_DECIMAL", "TIPO_CADENA", "TIPO_ECUACION", 
                    "TIPO_POSITIVO", "TIPO_BINARIO", "TIPO_CHAIN"]:
            self.analizar_declaracion()
            return
        
        # Asignaciones
        if tipo == "IDENTIFICADOR":
            siguiente = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if siguiente and siguiente[1] in ["ASIGNACION", "MAS_IGUAL", "MENOS_IGUAL"]:
                self.analizar_asignacion()
                return
            elif siguiente and siguiente[1] in ["INCREMENTO", "DECREMENTO"]:
                self.analizar_incremento_decremento()
                return
        
        # Funciones de salida
        if tipo == "FUNCION_PRI":
            self.analizar_pri()
            return
        
        # Funciones de entrada
        if tipo == "FUNCION_PUT":
            self.analizar_put()
            return
        
        # Control de flujo
        if tipo == "CONDICIONAL_IF":
            self.analizar_if()
            return
        
        if tipo == "BUCLE_WHILE":
            self.analizar_while()
            return
        
        # Funciones gráficas
        if tipo in ["FUNCION_DIBUJO_2D", "FUNCION_DIBUJO_3D", "FUNCION_PLANO_2D", 
                    "FUNCION_TEXTO", "FUNCION_MOVE", "FUNCION_NOW", "FUNCION_LOST"]:
            self.analizar_funcion_grafica(lexema, tipo)
            return
        
        # Contextos gráficos
        if tipo in ["VENTANA_2D", "VENTANA_3D", "FUNCION_DISPLAY"]:
            self.analizar_contexto_grafico()
            return
        
        # Funciones de evaluación
        if tipo in ["FUNCION_EVA", "FUNCION_REM", "FUNCION_FACT"]:
            self.analizar_funcion_matematica()
            return
        
        # Avanzar si no coincide con nada
        self.avanzar()
    
    def analizar_declaracion(self):
        """3.2. Errores en Declaraciones"""
        tipo_token, _ = self.actual()
        tipo_var = tipo_token
        self.avanzar()
        
        if self.actual()[1] != "IDENTIFICADOR":
            self.errores.append("Error semántico: se esperaba nombre de variable en declaración")
            return
        
        nombre_var = self.actual()[0]
        self.avanzar()
        
        # 3.2.2. Redefinición de símbolo en el mismo ámbito
        ambito_actual = self.pila_ambitos[-1]
        if nombre_var in ambito_actual:
            self.errores.append(f"Error semántico: redefinición de '{nombre_var}' en el mismo ámbito.")
            return
        
        # Verificar inicialización
        tiene_inicializacion = False
        tipo_inicializacion = None
        
        if self.actual()[1] == "ASIGNACION":
            tiene_inicializacion = True
            self.avanzar()
            tipo_inicializacion = self.analizar_expresion()
            
            # 3.2.3. Inicialización con tipo incompatible
            if not self.tipos_compatibles(tipo_var, tipo_inicializacion):
                self.errores.append(
                    f"Error semántico: tipo incompatible en inicialización de '{nombre_var}'. "
                    f"Se esperaba '{tipo_var}' pero se obtuvo '{tipo_inicializacion}'."
                )
        
        # Registrar símbolo
        ambito_actual[nombre_var] = {
            'tipo': self.normalizar_tipo(tipo_var),
            'inicializada': tiene_inicializacion,
            'ambito': self.ambito_actual
        }
        
        # Consumir punto y coma
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_asignacion(self):
        """3.3. Errores en Asignaciones"""
        nombre_var = self.actual()[0]
        self.avanzar()
        
        operador = self.actual()[1]
        self.avanzar()
        
        # 3.3.1. Asignación a símbolo no existente
        if not self.simbolo_existe(nombre_var):
            self.errores.append(f"Error semántico: símbolo '{nombre_var}' no declarado para asignación.")
            # Consumir resto de expresión
            self.consumir_hasta("PUNTO_COMA")
            return
        
        # Obtener tipo de variable
        info_var = self.obtener_info_simbolo(nombre_var)
        tipo_var = info_var['tipo']
        
        # Analizar expresión del lado derecho
        tipo_expr = self.analizar_expresion()
        
        # 3.3.2. Tipo incompatible en asignación
        if not self.tipos_compatibles(tipo_var, tipo_expr):
            self.errores.append(
                f"Error semántico: no se puede asignar expresión de tipo '{tipo_expr}' a '{nombre_var}' de tipo '{tipo_var}'."
            )
        
        # Marcar como inicializada
        info_var['inicializada'] = True
        
        # Consumir punto y coma
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_incremento_decremento(self):
        """3.3.3. Incremento en tipo no numérico"""
        nombre_var = self.actual()[0]
        self.avanzar()
        
        operador = self.actual()[0]  # ++ o --
        self.avanzar()
        
        # Verificar que existe
        if not self.simbolo_existe(nombre_var):
            self.errores.append(f"Error semántico: variable '{nombre_var}' no declarada.")
            return
        
        # Verificar que es numérico
        info_var = self.obtener_info_simbolo(nombre_var)
        if info_var['tipo'] not in ['int', 'dec', 'pos']:
            self.errores.append(
                f"Error semántico: {operador} aplicado a tipo no numérico '{info_var['tipo']}'."
            )
        
        # Consumir punto y coma
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_pri(self):
        """3.5.1. Salida de expresión no válida"""
        self.avanzar()  # consumir 'pri'
        
        if self.actual()[1] != "PAR_IZQ":
            self.errores.append("Error semántico: se esperaba '(' después de 'pri'")
            return
        
        self.avanzar()  # consumir '('
        
        # Analizar argumento
        lexema, tipo = self.actual()
        
        if tipo == "CADENA":
            # Las cadenas son válidas
            self.avanzar()
        elif tipo == "IDENTIFICADOR":
            # Verificar que la variable existe
            if not self.simbolo_existe(lexema):
                self.errores.append(f"Error semántico: argumento no válido en 'pri'. Variable '{lexema}' no declarada.")
            self.avanzar()
        elif tipo in ["NUMERO", "EXPRESION_MATH"]:
            self.avanzar()
        else:
            # Intentar analizar como expresión
            tipo_expr = self.analizar_expresion()
        
        if self.actual()[1] == "PAR_DER":
            self.avanzar()
        
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_put(self):
        """Entrada de usuario"""
        self.avanzar()  # consumir 'put'
        
        if self.actual()[1] != "PAR_IZQ":
            return
        
        self.avanzar()  # consumir '('
        
        if self.actual()[1] == "IDENTIFICADOR":
            nombre_var = self.actual()[0]
            
            # 3.2.1. Variable no declarada
            if not self.simbolo_existe(nombre_var):
                self.errores.append(f"Error semántico: variable '{nombre_var}' no declarada para 'put'.")
            else:
                # Marcar como inicializada
                info = self.obtener_info_simbolo(nombre_var)
                info['inicializada'] = True
            
            self.avanzar()
        
        if self.actual()[1] == "PAR_DER":
            self.avanzar()
        
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_if(self):
        """3.6.1. Condición no booleana"""
        self.avanzar()  # consumir 'if'
        
        if self.actual()[1] != "PAR_IZQ":
            return
        
        self.avanzar()  # consumir '('
        
        # Analizar condición
        tipo_condicion = self.analizar_expresion()
        
        # Verificar que es booleana (comparación)
        if tipo_condicion not in ['bool', 'comparacion']:
            # Buscar si hay operadores de comparación
            if not self.tiene_operador_comparacion():
                self.advertencias.append(
                    "Advertencia semántica: la condición debería ser una expresión booleana o comparación explícita."
                )
        
        if self.actual()[1] == "PAR_DER":
            self.avanzar()
        
        # Analizar bloque
        if self.actual()[1] == "LLAVE_IZQ":
            self.entrar_nuevo_ambito()
            self.avanzar()
            
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.analizar_instruccion()
            
            if self.actual()[1] == "LLAVE_DER":
                self.avanzar()
            
            self.salir_ambito()
        
        # Manejar elif/else
        while self.actual()[1] in ["CONDICIONAL_ELIF", "CONDICIONAL_ELSE"]:
            if self.actual()[1] == "CONDICIONAL_ELIF":
                self.avanzar()
                if self.actual()[1] == "PAR_IZQ":
                    self.avanzar()
                    self.analizar_expresion()
                    if self.actual()[1] == "PAR_DER":
                        self.avanzar()
            else:
                self.avanzar()  # consumir 'else'
            
            if self.actual()[1] == "LLAVE_IZQ":
                self.entrar_nuevo_ambito()
                self.avanzar()
                
                while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                    self.analizar_instruccion()
                
                if self.actual()[1] == "LLAVE_DER":
                    self.avanzar()
                
                self.salir_ambito()
    
    def analizar_while(self):
        """Bucle while"""
        self.avanzar()  # consumir 'while'
        
        if self.actual()[1] != "PAR_IZQ":
            return
        
        self.avanzar()  # consumir '('
        
        # Analizar condición
        self.analizar_expresion()
        
        if self.actual()[1] == "PAR_DER":
            self.avanzar()
        
        # Analizar bloque
        if self.actual()[1] == "LLAVE_IZQ":
            self.entrar_nuevo_ambito()
            self.avanzar()
            
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.analizar_instruccion()
            
            if self.actual()[1] == "LLAVE_DER":
                self.avanzar()
            
            self.salir_ambito()
    
    def analizar_funcion_grafica(self, nombre, tipo):
        """3.8.1. Sentencia gráfica fuera de contexto"""
        # draw2d, draw3d, text, move, now, lost requieren contexto gráfico
        if tipo in ["FUNCION_DIBUJO_2D", "FUNCION_DIBUJO_3D"]:
            # Permitir draw2d y draw3d fuera de contexto (según tu código actual)
            pass
        elif tipo in ["FUNCION_TEXTO", "FUNCION_MOVE", "FUNCION_NOW", "FUNCION_LOST"]:
            # 3.9.1. Animación fuera de contexto gráfico
            if not self.en_contexto_grafico:
                self.errores.append(
                    f"Error semántico: '{nombre}' solo es válida dentro de contextos de visualización "
                    f"(display, win2d, win3d)."
                )
        
        # Consumir función completa
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
        
        if self.actual()[1] == "PUNTO_COMA":
            self.avanzar()
    
    def analizar_contexto_grafico(self):
        """Analiza win2d, win3d, display"""
        self.avanzar()  # consumir palabra clave
        
        if self.actual()[1] == "IDENTIFICADOR":
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
        
        # Entrar en contexto gráfico
        if self.actual()[1] == "LLAVE_IZQ":
            self.en_contexto_grafico = True
            self.entrar_nuevo_ambito()
            self.avanzar()
            
            while self.actual()[1] not in ["LLAVE_DER", "EOF"]:
                self.analizar_instruccion()
            
            if self.actual()[1] == "LLAVE_DER":
                self.avanzar()
            
            self.salir_ambito()
            self.en_contexto_grafico = False
    
    def analizar_funcion_matematica(self):
        """3.4.1. Invocación de función simbólica con parámetros incorrectos"""
        nombre_func = self.actual()[0]
        self.avanzar()
        
        if self.actual()[1] == "PAR_IZQ":
            # Por ahora solo consumir, se podría validar firma
            depth = 1
            self.avanzar()
            while depth > 0 and self.actual()[1] != "EOF":
                if self.actual()[1] == "PAR_IZQ":
                    depth += 1
                elif self.actual()[1] == "PAR_DER":
                    depth -= 1
                self.avanzar()
    
    def analizar_expresion(self):
        """Analiza una expresión y retorna su tipo"""
        lexema, tipo = self.actual()
        
        if tipo == "NUMERO":
            self.avanzar()
            return "int" if '.' not in lexema else "dec"
        
        elif tipo == "CADENA":
            self.avanzar()
            return "string"
        
        elif tipo == "EXPRESION_MATH":
            self.avanzar()
            return "ecu"
        
        elif tipo == "IDENTIFICADOR":
            if not self.simbolo_existe(lexema):
                self.errores.append(f"Error semántico: variable '{lexema}' no declarada.")
                self.avanzar()
                return "unknown"
            
            info = self.obtener_info_simbolo(lexema)
            self.avanzar()
            
            # Verificar operadores
            if self.actual()[1] in ["MAS", "MENOS", "MULT", "DIV", "POTENCIA", "MOD"]:
                # Operación aritmética
                self.avanzar()
                tipo_derecha = self.analizar_expresion()
                return self.resolver_tipo_operacion(info['tipo'], tipo_derecha)
            
            elif self.actual()[1] in ["MENOR", "MAYOR", "IGUAL", "DIFERENTE", "MENORIGUAL", "MAYORIGUAL"]:
                # Comparación
                self.avanzar()
                self.analizar_expresion()
                return "bool"
            
            return info['tipo']
        
        elif tipo == "PAR_IZQ":
            self.avanzar()
            tipo_interno = self.analizar_expresion()
            if self.actual()[1] == "PAR_DER":
                self.avanzar()
            return tipo_interno
        
        elif tipo in ["BOOLEANO_TRUE", "BOOLEANO_FALSE"]:
            self.avanzar()
            return "bool"
        
        elif tipo in ["FUNCION_MATH", "FUNCION_REM", "FUNCION_EVA", "FUNCION_FACT"]:
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
            return "dec"
        
        else:
            # Avanzar para no quedarse atascado
            if tipo not in ["PUNTO_COMA", "PAR_DER", "COMA", "EOF"]:
                self.avanzar()
            return "unknown"
    
    # ===== MÉTODOS AUXILIARES =====
    
    def entrar_nuevo_ambito(self):
        """Crea un nuevo ámbito"""
        self.ambito_actual += 1
        self.pila_ambitos.append({})
    
    def salir_ambito(self):
        """Sale del ámbito actual"""
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()
            self.ambito_actual -= 1
    
    def simbolo_existe(self, nombre):
        """Verifica si un símbolo existe en cualquier ámbito"""
        for ambito in reversed(self.pila_ambitos):
            if nombre in ambito:
                return True
        return False
    
    def obtener_info_simbolo(self, nombre):
        """Obtiene información de un símbolo"""
        for ambito in reversed(self.pila_ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None
    
    def normalizar_tipo(self, tipo_token):
        """Convierte token de tipo a nombre de tipo"""
        mapeo = {
            "int": "int",
            "dec": "dec",
            "string": "string",
            "ecu": "ecu",
            "pos": "pos",
            "bin": "bin",
            "chain": "chain"
        }
        return mapeo.get(tipo_token.lower(), tipo_token)
    
    def tipos_compatibles(self, tipo_destino, tipo_origen):
        """Verifica si dos tipos son compatibles"""
        tipo_destino = self.normalizar_tipo(tipo_destino)
        tipo_origen = self.normalizar_tipo(tipo_origen)
        
        if tipo_destino == tipo_origen:
            return True
        
        # Conversiones permitidas
        if tipo_destino == "dec" and tipo_origen == "int":
            return True
        
        if tipo_destino == "pos" and tipo_origen == "int":
            return True
        
        if tipo_origen == "unknown":
            return True  # No sabemos, no reportar error
        
        return False
    
    def resolver_tipo_operacion(self, tipo1, tipo2):
        """Resuelve el tipo resultante de una operación"""
        if tipo1 == "dec" or tipo2 == "dec":
            return "dec"
        if tipo1 == "int" and tipo2 == "int":
            return "int"
        return "dec"
    
    def tiene_operador_comparacion(self):
        """Verifica si hay un operador de comparación cercano"""
        for i in range(max(0, self.pos - 3), min(len(self.tokens), self.pos + 3)):
            if self.tokens[i][1] in ["MENOR", "MAYOR", "IGUAL", "DIFERENTE", "MENORIGUAL", "MAYORIGUAL"]:
                return True
        return False
    
    def consumir_hasta(self, tipo_token):
        """Consume tokens hasta encontrar el especificado"""
        while self.actual()[1] != tipo_token and self.actual()[1] != "EOF":
            self.avanzar()
        if self.actual()[1] == tipo_token:
            self.avanzar()
