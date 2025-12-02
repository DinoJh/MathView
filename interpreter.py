import re
import ast
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from matplotlib.animation import FuncAnimation, PillowWriter

# Configuración de matplotlib
plt.style.use('dark_background')
plt.rcParams.update({
    'figure.facecolor': '#0a0e27',
    'axes.facecolor': '#111827',
    'axes.edgecolor': '#4ade80',
    'axes.labelcolor': '#e0e7ff',
    'axes.grid': True,
    'grid.color': '#1e293b',
    'grid.alpha': 0.3,
    'grid.linewidth': 0.8,
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'text.color': '#e0e7ff',
    'font.size': 11,
    'font.family': 'sans-serif',
    'lines.linewidth': 2.5,
    'lines.antialiased': True,
    'figure.dpi': 100,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
    'savefig.facecolor': '#0a0e27'
})

# Utilidades de evaluación segura
_SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_NUMPY = {
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'exp': np.exp, 'log': np.log, 'ln': np.log, 'sqrt': np.sqrt,
    'abs': np.abs, 'pi': np.pi, 'e': np.e,
    'arctan2': np.arctan2, 'arcsin': np.arcsin,
    'arccos': np.arccos, 'sinh': np.sinh, 'cosh': np.cosh
}
_SAFE_NAMES = {}
_SAFE_NAMES.update(_SAFE_MATH)
_SAFE_NAMES.update(_SAFE_NUMPY)

def factorial(n):
    """Calcula factorial"""
    if n <= 1:
        return 1
    result = 1
    for i in range(2, int(n) + 1):
        result *= i
    return result

_SAFE_NAMES['fact'] = factorial

def compile_expr_1d(expr_src):
    """Crea función f(x) que evalúa expr_src de forma segura."""
    try:
        expr_src = expr_src.replace('^', '**')
        node = ast.parse(expr_src, mode='eval')
        
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if not isinstance(sub.func, ast.Name):
                    raise ValueError("Llamadas complejas no permitidas")
            elif isinstance(sub, ast.Attribute):
                raise ValueError("Acceso por atributo no permitido")
            elif isinstance(sub, (ast.Import, ast.ImportFrom, ast.Lambda)):
                raise ValueError("Constructos no permitidos")
        
        code = compile(node, filename="<expr>", mode="eval")
        
        def f(x):
            env = {'x': x, 'b': x}
            env.update(_SAFE_NAMES)
            return eval(code, {"__builtins__": {}}, env)
        return f
    except Exception as e:
        raise ValueError(f"Error compilando expresión: {e}")

def compile_expr_2d(expr_src):
    """Crea función f(x,y) que evalúa expr_src."""
    try:
        expr_src = expr_src.replace('^', '**')
        node = ast.parse(expr_src, mode='eval')
        
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if not isinstance(sub.func, ast.Name):
                    raise ValueError("Llamadas complejas no permitidas")
            elif isinstance(sub, ast.Attribute):
                raise ValueError("Acceso por atributo no permitido")
            elif isinstance(sub, (ast.Import, ast.ImportFrom, ast.Lambda)):
                raise ValueError("Constructos no permitidos")
        
        code = compile(node, filename="<expr2d>", mode="eval")
        
        def f(x, y):
            env = {'x': x, 'y': y}
            env.update(_SAFE_NAMES)
            return eval(code, {"__builtins__": {}}, env)
        return f
    except Exception as e:
        raise ValueError(f"Error compilando expresión 2D: {e}")

def png_from_figure(fig, dpi=100):
    """Convierte figura matplotlib a PNG base64."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
    buf.seek(0)
    data64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data64

class Interpreter:
    def __init__(self, source_code, user_inputs=None):
        self.source = source_code if isinstance(source_code, str) else ""
        self.variables = {}
        self.salida_consola = []
        self.ultima_imagen = None
        self.tipo_imagen = "png"
        self.actions = []
        self.user_inputs = user_inputs if user_inputs else []
        self.input_index = 0
        self.solicitudes_input = []
        self.errores = []

    def ejecutar(self):
        """Ejecuta el código y retorna resultados."""
        try:
            if not self.source or not self.source.strip():
                self.errores.append("⚠️ Código vacío")
                return self.get_result()

            # CAMBIO CRÍTICO: Ejecutar código secuencialmente SIEMPRE
            # Esto permite que las condicionales controlen qué gráficas se dibujan
            self.ejecutar_codigo_secuencial()

        except Exception as e:
            self.errores.append(f"Error en ejecución: {str(e)}")

        return self.get_result()

    def get_result(self):
        """Retorna el resultado de la ejecución."""
        return {
            "texto": "\n".join(self.salida_consola),
            "errores": self.errores,
            "imagen": self.ultima_imagen,
            "tipo_imagen": self.tipo_imagen,
            "acciones": self.actions,
            "solicitudes_input": self.solicitudes_input
        }

    def ejecutar_codigo_secuencial(self):
        """Ejecuta código línea por línea"""
        lineas = self.source.split(';')
        
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            
            if not linea:
                i += 1
                continue
            
            # Si hay solicitudes de input pendientes, detener ejecución
            if self.solicitudes_input:
                break
            
            # Detectar bloques while
            if 'while' in linea and '{' in linea:
                bloque_completo = linea
                nivel_llaves = linea.count('{') - linea.count('}')
                j = i + 1
                
                while nivel_llaves > 0 and j < len(lineas):
                    bloque_completo += ';' + lineas[j]
                    nivel_llaves += lineas[j].count('{') - lineas[j].count('}')
                    j += 1
                
                self.ejecutar_while(bloque_completo)
                i = j
                continue
            
            # Detectar bloques if
            if linea.startswith('if') and '(' in linea:
                bloque_completo = linea
                nivel_llaves = linea.count('{') - linea.count('}')
                j = i + 1
                
                while nivel_llaves > 0 and j < len(lineas):
                    bloque_completo += ';' + lineas[j]
                    nivel_llaves += lineas[j].count('{') - lineas[j].count('}')
                    j += 1
                
                # Buscar else if o else
                while j < len(lineas):
                    siguiente = lineas[j].strip()
                    if siguiente.startswith('elif') or siguiente.startswith('else'):
                        bloque_completo += ';' + siguiente
                        if '{' in siguiente:
                            nivel_llaves = siguiente.count('{') - siguiente.count('}')
                            j += 1
                            while nivel_llaves > 0 and j < len(lineas):
                                bloque_completo += ';' + lineas[j]
                                nivel_llaves += lineas[j].count('{') - lineas[j].count('}')
                                j += 1
                        else:
                            j += 1
                    else:
                        break
                
                self.ejecutar_if(bloque_completo)
                i = j
                continue
            
            # Instrucción individual
            try:
                self.ejecutar_instruccion(linea)
                # Si se solicitó input, detener
                if self.solicitudes_input:
                    break
            except StopIteration:
                # Se necesita input, detener ejecución
                break
            except Exception as e:
                self.errores.append(f"Error: {str(e)}")
            
            i += 1

    def ejecutar_instruccion(self, linea):
        """Ejecuta una instrucción individual"""
        linea = linea.strip()
        
        if not linea or linea == '}' or linea == '{':
            return
        
        # Si ya tenemos solicitudes de input pendientes, no seguir ejecutando
        if self.solicitudes_input:
            return
        
        # draw2d(...)
        if linea.startswith('draw2d('):
            self.ejecutar_draw2d(linea)
            return
        
        # draw3d(...)
        if linea.startswith('draw3d('):
            self.ejecutar_draw3d(linea)
            return
        
        # Declaración con tipo
        if re.match(r'^\s*(int|dec|ecu|string)\s+\w+', linea):
            self.ejecutar_declaracion(linea)
            return
        
        # Asignación
        if re.match(r'^\s*\w+\s*=', linea):
            self.ejecutar_asignacion(linea)
            return
        
        # pri(...)
        if linea.startswith('pri('):
            self.ejecutar_pri(linea)
            return
        
        # put(...) - Solicitar entrada
        if linea.startswith('put('):
            self.ejecutar_put(linea)
            return
        
        # Incremento/decremento
        if re.match(r'^\s*\w+\s*\+\+', linea):
            var = re.match(r'(\w+)\s*\+\+', linea).group(1)
            if var in self.variables:
                self.variables[var] += 1
            return
        
        if re.match(r'^\s*\w+\s*--', linea):
            var = re.match(r'(\w+)\s*--', linea).group(1)
            if var in self.variables:
                self.variables[var] -= 1
            return

    def ejecutar_draw2d(self, linea):
        """Ejecuta draw2d directamente"""
        match = re.match(r'draw2d\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)', linea)
        if match:
            expr, xmin_str, xmax_str = match.groups()
            try:
                xmin = float(self.evaluar_expresion(xmin_str.strip()))
                xmax = float(self.evaluar_expresion(xmax_str.strip()))
                self.crear_grafico_2d(expr.strip(), xmin, xmax)
            except Exception as e:
                self.errores.append(f"Error en draw2d: {e}")

    def ejecutar_draw3d(self, linea):
        """Ejecuta draw3d directamente"""
        match = re.match(r'draw3d\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)', linea)
        if match:
            expr, xmin_str, xmax_str, ymin_str, ymax_str = match.groups()
            try:
                xmin = float(self.evaluar_expresion(xmin_str.strip()))
                xmax = float(self.evaluar_expresion(xmax_str.strip()))
                ymin = float(self.evaluar_expresion(ymin_str.strip()))
                ymax = float(self.evaluar_expresion(ymax_str.strip()))
                self.crear_grafico_3d(expr.strip(), xmin, xmax, ymin, ymax)
            except Exception as e:
                self.errores.append(f"Error en draw3d: {e}")

    def ejecutar_declaracion(self, linea):
        """int n = 10; o int n;"""
        match = re.match(r'(int|dec|ecu|string)\s+(\w+)(?:\s*=\s*(.+))?', linea)
        if match:
            tipo, var, valor = match.groups()
            
            if valor:
                if valor.startswith('//') and valor.endswith('//'):
                    valor_limpio = valor[2:-2].strip()
                    self.variables[var] = valor_limpio
                else:
                    self.variables[var] = self.evaluar_expresion(valor)
            else:
                valor_default = 0 if tipo in ['int', 'dec'] else ""
                self.variables[var] = valor_default

    def ejecutar_asignacion(self, linea):
        """n = 10; o n = n + 1;"""
        match = re.match(r'(\w+)\s*=\s*(.+)', linea)
        if match:
            var, expr = match.groups()
            self.variables[var] = self.evaluar_expresion(expr)

    def ejecutar_pri(self, linea):
        """pri(n); o pri("texto");"""
        match = re.match(r'pri\s*\(\s*(.+?)\s*\)', linea)
        if match:
            contenido = match.group(1).strip()
            
            # Cadena
            if (contenido.startswith('"') and contenido.endswith('"')) or \
               (contenido.startswith("'") and contenido.endswith("'")):
                texto = contenido[1:-1]
                self.salida_consola.append(texto)
            # Expresión //...//
            elif contenido.startswith('//') and contenido.endswith('//'):
                expr = contenido[2:-2]
                self.salida_consola.append(expr)
            # Variable
            elif contenido in self.variables:
                self.salida_consola.append(str(self.variables[contenido]))
            # Expresión
            else:
                valor = self.evaluar_expresion(contenido)
                self.salida_consola.append(str(valor))

    def ejecutar_put(self, linea):
        """put(n); - solicita entrada del usuario"""
        match = re.match(r'put\s*\(\s*(\w+)\s*\)', linea)
        if match:
            var = match.group(1)
            
            # Si hay inputs proporcionados, usar el siguiente
            if self.input_index < len(self.user_inputs):
                valor_str = self.user_inputs[self.input_index]
                self.input_index += 1
                
                # Intentar convertir a número
                try:
                    if '.' in valor_str:
                        valor = float(valor_str)
                    else:
                        valor = int(valor_str)
                except:
                    valor = valor_str
                
                self.variables[var] = valor
                # No agregar a salida aquí, ya se muestra en el frontend
            else:
                # Solicitar input al usuario SOLO si no lo hemos pedido ya
                if not self.solicitudes_input or self.solicitudes_input[-1]['variable'] != var:
                    self.solicitudes_input.append({
                        'variable': var,
                        'mensaje': f'Ingrese valor para {var}:'
                    })
                # Detener ejecución hasta recibir input
                raise StopIteration("Esperando input del usuario")

    def ejecutar_while(self, bloque):
        """Ejecuta bucle while"""
        match = re.match(r'while\s*\(\s*(.+?)\s*\)\s*\{(.+)\}', bloque, re.DOTALL)
        if not match:
            self.errores.append("Error: sintaxis de while incorrecta")
            return
        
        condicion_str, cuerpo = match.groups()
        
        iteraciones = 0
        max_iter = 1000
        
        while iteraciones < max_iter:
            try:
                condicion = self.evaluar_expresion(condicion_str)
                if not condicion:
                    break
            except:
                break
            
            instrucciones = cuerpo.split(';')
            for inst in instrucciones:
                inst = inst.strip()
                if inst:
                    self.ejecutar_instruccion(inst)
            
            iteraciones += 1

    def ejecutar_if(self, bloque):
        """Ejecuta condicional if/elif/else"""
        # Extraer if principal
        match_if = re.match(r'if\s*\(\s*(.+?)\s*\)\s*\{(.+?)(?=\}\s*(?:elif|else)|$)', bloque, re.DOTALL)
        if not match_if:
            self.errores.append("Error: sintaxis de if incorrecta")
            return
        
        condicion_if, cuerpo_if = match_if.groups()
        
        # Evaluar if
        try:
            if self.evaluar_expresion(condicion_if):
                # Ejecutar bloque if
                instrucciones = cuerpo_if.split(';')
                for inst in instrucciones:
                    inst = inst.strip()
                    if inst and inst != '}':
                        self.ejecutar_instruccion(inst)
                return  # Si el if se ejecutó, no evaluar elif/else
        except Exception as e:
            self.errores.append(f"Error en if: {e}")
            return
        
        # Buscar elif
        resto = bloque[match_if.end():]
        matches_elif = list(re.finditer(r'(?:elif)\s*\(\s*(.+?)\s*\)\s*\{(.+?)\}', resto, re.DOTALL))
        
        for match_elif in matches_elif:
            condicion_elif, cuerpo_elif = match_elif.groups()
            try:
                if self.evaluar_expresion(condicion_elif):
                    instrucciones = cuerpo_elif.split(';')
                    for inst in instrucciones:
                        inst = inst.strip()
                        if inst and inst != '}':
                            self.ejecutar_instruccion(inst)
                    return  # Si un elif se ejecutó, terminar
            except:
                continue
        
        # Buscar else
        match_else = re.search(r'else\s*\{(.+?)\}', resto, re.DOTALL)
        if match_else:
            cuerpo_else = match_else.group(1)
            instrucciones = cuerpo_else.split(';')
            for inst in instrucciones:
                inst = inst.strip()
                if inst and inst != '}':
                    self.ejecutar_instruccion(inst)

    def evaluar_expresion(self, expr):
        """Evalúa una expresión matemática"""
        try:
            expr = str(expr).strip()
            
            # Reemplazar variables
            for var, val in self.variables.items():
                expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), expr)
            
            expr = expr.replace('^', '**')
            
            env = dict(_SAFE_NAMES)
            resultado = eval(expr, {"__builtins__": {}}, env)
            
            return resultado
        except Exception as e:
            return expr

    def crear_grafico_2d(self, expr, xmin, xmax):
        """Crea gráfico 2D"""
        try:
            expr_py = expr.replace('^', '**')
            f = compile_expr_1d(expr_py)
            
            x = np.linspace(xmin, xmax, 800)
            y = f(x)
            
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(x, y, color='deepskyblue', linewidth=2, label=f'y = {expr}')
            ax.set_title(f'Gráfico 2D: y = {expr}', fontsize=14, fontweight='bold')
            ax.set_xlabel('x', fontsize=12)
            ax.set_ylabel('y', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            self.ultima_imagen = png_from_figure(fig)
            self.tipo_imagen = "png"
            self.salida_consola.append(f"✓ Gráfico 2D generado")
            
        except Exception as e:
            self.errores.append(f"Error en gráfico 2D: {str(e)}")

    def crear_grafico_3d(self, expr, xmin, xmax, ymin, ymax):
        """Crea gráfico 3D"""
        try:
            expr_py = expr.replace('^', '**')
            f2 = compile_expr_2d(expr_py)
            
            X = np.linspace(xmin, xmax, 100)
            Y = np.linspace(ymin, ymax, 100)
            XX, YY = np.meshgrid(X, Y)
            Z = f2(XX, YY)
            
            from mpl_toolkits.mplot3d import Axes3D
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111, projection='3d')
            surf = ax.plot_surface(XX, YY, Z, cmap='viridis', alpha=0.9)
            ax.set_title(f'Gráfico 3D: z = {expr}', fontsize=14, fontweight='bold')
            ax.set_xlabel('X', fontsize=11)
            ax.set_ylabel('Y', fontsize=11)
            ax.set_zlabel('Z', fontsize=11)
            fig.colorbar(surf, shrink=0.5, aspect=5)
            
            self.ultima_imagen = png_from_figure(fig, dpi=100)
            self.tipo_imagen = "png"
            self.salida_consola.append(f"✓ Gráfico 3D generado")
            
        except Exception as e:
            self.errores.append(f"Error en gráfico 3D: {str(e)}")