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

def split_top_level_commas(s):
    """Separa argumentos por comas respetando paréntesis."""
    args = []
    depth = 0
    current = []
    
    for ch in s:
        if ch == ',' and depth == 0:
            arg = ''.join(current).strip()
            if arg:
                args.append(arg)
            current = []
            continue
        current.append(ch)
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    
    last = ''.join(current).strip()
    if last:
        args.append(last)
    return args

def png_from_figure(fig, dpi=100):
    """Convierte figura matplotlib a PNG base64."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
    buf.seek(0)
    data64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data64

def gif_from_animation(anim, fps=20):
    """Convierte animación a GIF base64."""
    buf = BytesIO()
    writer = PillowWriter(fps=fps)
    anim.save(buf, writer=writer, dpi=80)
    buf.seek(0)
    data64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close('all')
    return data64

class Interpreter:
    def __init__(self, source_code):
        self.source = source_code if isinstance(source_code, str) else ""
        self.variables = {}
        self.salida = []
        self.ultima_imagen = None
        self.tipo_imagen = "png"
        self.actions = []
        self.output_buffer = []

    def ejecutar(self):
        """Ejecuta el código y retorna resultados."""
        try:
            if not self.source or not self.source.strip():
                self.salida.append("⚠️ Código vacío")
                return self.get_result()

            # Buscar funciones gráficas primero (draw2d, draw3d, text)
            if self.tiene_funciones_graficas():
                self.ejecutar_funciones_graficas()
            else:
                # Ejecutar código línea por línea
                self.ejecutar_codigo_secuencial()

        except Exception as e:
            self.salida.append(f"❌ Error: {str(e)}")
            import traceback
            self.salida.append(traceback.format_exc())

        return self.get_result()

    def get_result(self):
        """Retorna el resultado de la ejecución."""
        return {
            "texto": "\n".join(self.salida),
            "imagen": self.ultima_imagen,
            "tipo_imagen": self.tipo_imagen,
            "acciones": self.actions
        }

    def tiene_funciones_graficas(self):
        """Detecta si hay funciones gráficas en el código"""
        return bool(re.search(r'\b(draw2d|draw3d|text|plane2d|plane3d)\s*\(', self.source))

    def ejecutar_funciones_graficas(self):
        """Ejecuta funciones gráficas (compatibilidad con código original)"""
        # Patrón para draw2d(expr, xmin, xmax)
        pattern_2d = re.compile(r'draw2d\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)', re.IGNORECASE)
        matches_2d = pattern_2d.findall(self.source)
        
        for match in matches_2d:
            expr, xmin_str, xmax_str = match
            try:
                xmin = float(eval(xmin_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                xmax = float(eval(xmax_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                self.crear_grafico_2d_simple(expr.strip(), xmin, xmax)
            except Exception as e:
                self.salida.append(f"❌ Error en draw2d: {e}")

        # Patrón para draw3d(expr, xmin, xmax, ymin, ymax)
        pattern_3d = re.compile(r'draw3d\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)', re.IGNORECASE)
        matches_3d = pattern_3d.findall(self.source)
        
        for match in matches_3d:
            expr, xmin_str, xmax_str, ymin_str, ymax_str = match
            try:
                xmin = float(eval(xmin_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                xmax = float(eval(xmax_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                ymin = float(eval(ymin_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                ymax = float(eval(ymax_str.strip(), {"__builtins__": {}}, _SAFE_NAMES))
                self.crear_grafico_3d_simple(expr.strip(), xmin, xmax, ymin, ymax)
            except Exception as e:
                self.salida.append(f"❌ Error en draw3d: {e}")

        # Patrón para text
        pattern_text = re.compile(r'text\s*\(\s*"([^"]+)"\s*\)', re.IGNORECASE)
        matches_text = pattern_text.findall(self.source)
        
        for texto in matches_text:
            self.salida.append(f"📝 {texto}")

    def ejecutar_codigo_secuencial(self):
        """Ejecuta código línea por línea (nuevo sistema)"""
        lineas = self.source.split(';')
        
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            
            if not linea:
                i += 1
                continue
            
            # Detectar bucles while
            if 'while' in linea and '{' in linea:
                # Buscar el cierre del bucle
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
            
            # Ejecutar instrucción individual
            try:
                self.ejecutar_instruccion(linea)
            except Exception as e:
                self.salida.append(f"❌ Error en línea: {str(e)}")
            
            i += 1

    def ejecutar_instruccion(self, linea):
        """Ejecuta una instrucción individual"""
        linea = linea.strip()
        
        if not linea or linea == '}' or linea == '{':
            return
        
        # Declaración con tipo: int n = 10;
        if re.match(r'^\s*(int|dec|ecu|string)\s+\w+', linea):
            self.ejecutar_declaracion(linea)
            return
        
        # Asignación: n = 10;
        if re.match(r'^\s*\w+\s*=', linea):
            self.ejecutar_asignacion(linea)
            return
        
        # pri(...)
        if linea.startswith('pri('):
            self.ejecutar_pri(linea)
            return
        
        # put(...)
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

    def ejecutar_declaracion(self, linea):
        """int n = 10; o int n;"""
        match = re.match(r'(int|dec|ecu|string)\s+(\w+)(?:\s*=\s*(.+))?', linea)
        if match:
            tipo, var, valor = match.groups()
            
            if valor:
                # Limpiar expresiones //...//
                if valor.startswith('//') and valor.endswith('//'):
                    valor_limpio = valor[2:-2].strip()
                    self.variables[var] = valor_limpio
                    self.salida.append(f"✓ {var} = {valor_limpio}")
                else:
                    self.variables[var] = self.evaluar_expresion(valor)
                    self.salida.append(f"✓ {var} = {self.variables[var]}")
            else:
                valor_default = 0 if tipo in ['int', 'dec'] else ""
                self.variables[var] = valor_default
                self.salida.append(f"✓ Variable {var} declarada")

    def ejecutar_asignacion(self, linea):
        """n = 10; o n = n + 1;"""
        match = re.match(r'(\w+)\s*=\s*(.+)', linea)
        if match:
            var, expr = match.groups()
            self.variables[var] = self.evaluar_expresion(expr)
            self.salida.append(f"✓ {var} = {self.variables[var]}")

    def ejecutar_pri(self, linea):
        """pri(n); o pri("texto");"""
        match = re.match(r'pri\s*\(\s*(.+?)\s*\)', linea)
        if match:
            contenido = match.group(1).strip()
            
            # Cadena
            if (contenido.startswith('"') and contenido.endswith('"')) or \
               (contenido.startswith("'") and contenido.endswith("'")):
                texto = contenido[1:-1]
                self.salida.append(f"📄 {texto}")
            # Expresión //...//
            elif contenido.startswith('//') and contenido.endswith('//'):
                expr = contenido[2:-2]
                self.salida.append(f"📄 {expr}")
            # Variable
            elif contenido in self.variables:
                self.salida.append(f"📄 {self.variables[contenido]}")
            # Expresión
            else:
                valor = self.evaluar_expresion(contenido)
                self.salida.append(f"📄 {valor}")

    def ejecutar_put(self, linea):
        """put(n); - solicita entrada"""
        match = re.match(r'put\s*\(\s*(\w+)\s*\)', linea)
        if match:
            var = match.group(1)
            self.variables[var] = 10  # Valor por defecto
            self.salida.append(f"📥 Entrada: {var} = 10")

    def ejecutar_while(self, bloque):
        """Ejecuta bucle while"""
        # Extraer condición y cuerpo
        match = re.match(r'while\s*\(\s*(.+?)\s*\)\s*\{(.+)\}', bloque, re.DOTALL)
        if not match:
            self.salida.append("❌ Error: sintaxis de while incorrecta")
            return
        
        condicion_str, cuerpo = match.groups()
        
        # Ejecutar bucle (máximo 1000 iteraciones para seguridad)
        iteraciones = 0
        max_iter = 1000
        
        while iteraciones < max_iter:
            # Evaluar condición
            try:
                condicion = self.evaluar_expresion(condicion_str)
                if not condicion:
                    break
            except:
                break
            
            # Ejecutar cuerpo
            instrucciones = cuerpo.split(';')
            for inst in instrucciones:
                inst = inst.strip()
                if inst:
                    self.ejecutar_instruccion(inst)
            
            iteraciones += 1
        
        self.salida.append(f"✓ Bucle while ejecutado ({iteraciones} iteraciones)")

    def evaluar_expresion(self, expr):
        """Evalúa una expresión matemática"""
        try:
            expr = str(expr).strip()
            
            # Reemplazar variables
            for var, val in self.variables.items():
                # Usar word boundary para evitar reemplazos parciales
                expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), expr)
            
            # Operadores relacionales
            expr = expr.replace('^', '**')
            
            # Evaluar
            env = dict(_SAFE_NAMES)
            resultado = eval(expr, {"__builtins__": {}}, env)
            
            return resultado
        except Exception as e:
            return expr

    def crear_grafico_2d_simple(self, expr, xmin, xmax):
        """Crea gráfico 2D simple"""
        try:
            expr_py = expr.replace('^', '**')
            f = compile_expr_1d(expr_py)
            
            x = np.linspace(xmin, xmax, 800)
            y = f(x)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(x, y, color='deepskyblue', linewidth=2, label=f'y = {expr}')
            ax.set_title(f'Gráfico 2D: y = {expr}', fontsize=14, fontweight='bold')
            ax.set_xlabel('x', fontsize=12)
            ax.set_ylabel('y', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            self.ultima_imagen = png_from_figure(fig)
            self.tipo_imagen = "png"
            self.salida.append(f"✓ Gráfico 2D: {expr}")
            self.actions.append({'type': 'draw2d', 'expr': expr})
            
        except Exception as e:
            self.salida.append(f"❌ Error en gráfico 2D: {str(e)}")

    def crear_grafico_3d_simple(self, expr, xmin, xmax, ymin, ymax):
        """Crea gráfico 3D simple"""
        try:
            expr_py = expr.replace('^', '**')
            f2 = compile_expr_2d(expr_py)
            
            X = np.linspace(xmin, xmax, 100)
            Y = np.linspace(ymin, ymax, 100)
            XX, YY = np.meshgrid(X, Y)
            Z = f2(XX, YY)
            
            from mpl_toolkits.mplot3d import Axes3D
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            surf = ax.plot_surface(XX, YY, Z, cmap='viridis', alpha=0.9)
            ax.set_title(f'Gráfico 3D: z = {expr}', fontsize=14, fontweight='bold')
            ax.set_xlabel('X', fontsize=11)
            ax.set_ylabel('Y', fontsize=11)
            ax.set_zlabel('Z', fontsize=11)
            fig.colorbar(surf, shrink=0.5, aspect=5)
            
            self.ultima_imagen = png_from_figure(fig, dpi=100)
            self.tipo_imagen = "png"
            self.salida.append(f"✓ Gráfico 3D: {expr}")
            self.actions.append({'type': 'draw3d', 'expr': expr})
            
        except Exception as e:
            self.salida.append(f"❌ Error en gráfico 3D: {str(e)}")