# interpreter.py
# Interpreter avanzado para el proyecto de compilador web
# - Analiza llamadas draw2d(...) / draw3d(...) desde el código fuente
# - Evalúa expresiones de forma segura usando ast
# - Genera PNG (base64) con matplotlib (o GIF si anim=True)
# - Retorna dict con "texto" y "imagen" (base64) y lista de "acciones" ejecutadas

import re
import ast
import math
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from matplotlib.animation import FuncAnimation, PillowWriter

# -------------------------
# Utilidades de evaluación segura
# -------------------------
# Permitir funciones math + numpy (nombres comunes)
_SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
# Añadir alias y numpy funciones que tengan sentido (vectorizadas)
_SAFE_NUMPY = {
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
    'abs': np.abs, 'pi': np.pi, 'e': np.e,
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'arctan2': np.arctan2
}
_SAFE_NAMES = {}
_SAFE_NAMES.update(_SAFE_MATH)
_SAFE_NAMES.update(_SAFE_NUMPY)
# x and y will be provided as numpy arrays during evaluation

# Analiza y compila expresion matemática a una función segura
def compile_expr_1d(expr_src):
    """
    Crea una función f(x) que evalúa expr_src. Usa ast para permitir solo expresiones.
    """
    node = ast.parse(expr_src, mode='eval')

    # Recorre AST y valida nodos permitidos
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            # permitir llamada a nombre simple (no atributos)
            if not isinstance(sub.func, ast.Name):
                raise ValueError("Llamadas complejas no permitidas")
        elif isinstance(sub, ast.Attribute):
            raise ValueError("Acceso por atributo no permitido")
        elif isinstance(sub, (ast.Import, ast.ImportFrom, ast.Lambda)):
            raise ValueError("Constructos no permitidos en expresiones")
        # otros nodos básicos (BinOp, Name, Num, UnaryOp, etc.) están bien

    code = compile(node, filename="<expr>", mode="eval")
    def f(x):
        env = {'x': x}
        env.update(_SAFE_NAMES)
        return eval(code, {"__builtins__": {}}, env)
    return f

def compile_expr_2d(expr_src):
    """
    Crea función f(x,y) que evalúa expr_src.
    """
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

# -------------------------
# Parsing simple de llamadas
# -------------------------
def split_top_level_commas(s):
    """Separa una lista de argumentos por comas a nivel top (ignora comas dentro de paréntesis)."""
    args = []
    depth = 0
    current = []
    for ch in s:
        if ch == ',' and depth == 0:
            arg = ''.join(current).strip()
            if arg: args.append(arg)
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

CALL_RE = re.compile(r'(?P<name>\b(?:draw2d|draw3d|win2d|win3d|text|plane2d|plane3d|display|move)\b)\s*\((?P<args>.*?)\)\s*;', re.S)

def extract_calls_from_source(source):
    """
    Devuelve lista de dicts: {name, raw_args, args_list}
    Encuentra todas las llamadas tipo ident(args...);
    """
    matches = CALL_RE.finditer(source)
    calls = []
    for m in matches:
        name = m.group('name')
        raw = m.group('args').strip()
        args = split_top_level_commas(raw)
        calls.append({'name': name, 'raw': raw, 'args': args})
    return calls

# -------------------------
# Funciones de graficado
# -------------------------
def png_from_figure(fig, close=True, dpi=100):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
    buf.seek(0)
    data64 = base64.b64encode(buf.read()).decode('utf-8')
    if close:
        plt.close(fig)
    return data64

def gif_from_animation(anim, close=True, fps=20):
    buf = BytesIO()
    writer = PillowWriter(fps=fps)
    anim.save(buf, writer=writer, dpi=80)
    buf.seek(0)
    data64 = base64.b64encode(buf.read()).decode('utf-8')
    if close:
        plt.close('all')
    return data64

# -------------------------
# Interpreter clase principal
# -------------------------
class Interpreter:
    def __init__(self, arbol_or_code):
        """
        Se acepta:
         - una lista 'arbol' (como antes) o
         - un string con el codigo fuente (recomendado para este intérprete avanzado)
        """
        if isinstance(arbol_or_code, str):
            self.source = arbol_or_code
            self.arbol = None
        else:
            # puede ser lista/AST; guardamos por compatibilidad y tratamos de reconstruir source vacío
            self.arbol = arbol_or_code
            self.source = None

        self.variables = {}
        self.salida = []
        self.ultima_imagen = None
        self.actions = []  # para logging de acciones realizadas

    def ejecutar(self):
        """
        Ejecuta el código: si tenemos source -> parsea llamadas; si solo arbol -> registra acciones simples.
        Retorna dict con 'texto', 'imagen' (base64) y 'acciones'.
        """
        try:
            if self.source:
                calls = extract_calls_from_source(self.source)
                if not calls:
                    self.salida.append("No se encontraron llamadas ejecutables en el código.")
                for call in calls:
                    self.execute_call(call)
            elif self.arbol:
                # Comportamiento de compatibilidad con arbol: solo registra nodos conocidos
                for nodo in self.arbol:
                    lower = str(nodo).lower()
                    if 'ventana' in lower:
                        self.salida.append("Ventana (de arbol) creada.")
                    elif 'draw2d' in lower:
                        # grafica x^2 por compatibilidad
                        self.plot_2d_static()
                    else:
                        self.salida.append(f"Ejecutado nodo: {nodo}")
            else:
                self.salida.append("Nada para ejecutar.")
        except Exception as e:
            self.salida.append(f"Error en ejecución: {str(e)}")

        return {
            "texto": "\n".join(self.salida),
            "imagen": self.ultima_imagen,
            "acciones": self.actions
        }

    # -------------------------
    # Ejecutar cada llamada parseada
    # -------------------------
    def execute_call(self, call):
        name = call['name']
        args = call['args']
        try:
            if name == 'draw2d':
                self.handle_draw2d(args)
            elif name == 'draw3d':
                self.handle_draw3d(args)
            elif name in ('win2d', 'win3d'):
                self.salida.append(f"Se creó ventana: {name} (parámetros: {args})")
                self.actions.append({'type': 'window', 'name': name, 'args': args})
            elif name == 'display':
                self.salida.append("Display llamado.")
            else:
                self.salida.append(f"Llamada reconocida: {name} (no implementada completamente)")
        except Exception as e:
            self.salida.append(f"Error al ejecutar {name}: {str(e)}")

    # -------------------------
    # handler draw2d
    # -------------------------
    def handle_draw2d(self, args):
        """
        Formatos esperados:
         draw2d(expr, xmin, xmax);
         draw2d(expr, xmin, xmax, anim=2);  # anim en segundos
         draw2d(expr, xmin, xmax, color="red");
        """
        if len(args) < 3:
            raise ValueError("draw2d requiere al menos 3 argumentos: expr, xmin, xmax")

        expr = args[0]
        xmin_s = args[1]
        xmax_s = args[2]

        # parse opcionales
        opts = {}
        for opt in args[3:]:
            if '=' in opt:
                k, v = opt.split('=', 1)
                opts[k.strip()] = v.strip()
            else:
                # strings sin clave, ignoramos o podríamos mapear
                pass

        # convertir limites
        try:
            xmin = float(eval(xmin_s, {"__builtins__": {}}, _SAFE_NAMES))
            xmax = float(eval(xmax_s, {"__builtins__": {}}, _SAFE_NAMES))
            if xmin >= xmax:
                raise ValueError("xmin debe ser menor que xmax")
        except Exception as e:
            raise ValueError(f"Errores al convertir límites: {e}")

        # Animación?
        anim_seconds = None
        if 'anim' in opts:
            try:
                anim_seconds = float(opts['anim'])
            except:
                anim_seconds = None

        # color opcional
        color = None
        if 'color' in opts:
            color = opts['color'].strip('"').strip("'")

        # preparar función evaluable
        # soportar ^ reemplazando por ** para potencias si el usuario lo escribió así
        expr_py = expr.replace('^', '**')
        f = compile_expr_1d(expr_py)

        # generar datos
        x = np.linspace(xmin, xmax, 800)
        try:
            y = f(x)
        except Exception as e:
            raise ValueError(f"Error al evaluar la expresión en rango: {e}")

        # chequeo de dimensiones y valores
        if np.shape(y) != np.shape(x):
            raise ValueError("La expresión no devolvió una salida compatible con x (debe ser función de x).")

        # Si anim_seconds -> crear animación progresiva y devolver GIF
        if anim_seconds and anim_seconds > 0:
            frames = int(anim_seconds * 20)  # 20 fps
            fig, ax = plt.subplots()
            ax.set_xlim(xmin, xmax)
            y_min, y_max = np.nanmin(y), np.nanmax(y)
            margin = (y_max - y_min) * 0.1 if (y_max - y_min) != 0 else 1.0
            ax.set_ylim(y_min - margin, y_max + margin)
            line, = ax.plot([], [], lw=2, color=color or 'deepskyblue')

            def init():
                line.set_data([], [])
                return (line,)

            def update(frame):
                idx = int(len(x) * (frame+1) / frames)
                line.set_data(x[:idx], y[:idx])
                return (line,)

            anim = FuncAnimation(fig, update, frames=frames, init_func=init, blit=True)
            gif64 = gif_from_animation(anim, close=True, fps=20)
            self.ultima_imagen = gif64
            self.salida.append(f"Animación draw2d({expr}) generada ({anim_seconds}s).")
            self.actions.append({'type': 'draw2d_anim', 'expr': expr, 'xmin': xmin, 'xmax': xmax})
            return

        # Si no anim -> PNG estático
        fig, ax = plt.subplots()
        ax.plot(x, y, color=color or 'deepskyblue', linewidth=2)
        ax.set_title(f"y = {expr}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True)
        png64 = png_from_figure(fig)
        self.ultima_imagen = png64
        self.salida.append(f"draw2d({expr}) generado correctamente.")
        self.actions.append({'type': 'draw2d', 'expr': expr, 'xmin': xmin, 'xmax': xmax})

    # -------------------------
    # handler draw3d
    # -------------------------
    def handle_draw3d(self, args):
        """
        Formatos esperados:
         draw3d(expr_xy, xmin, xmax, ymin, ymax);
         Opcionales: color, anim
         expr_xy debe ser función de x e y, p.ej: sin(sqrt(x**2+y**2))
        """
        if len(args) < 5:
            raise ValueError("draw3d requiere 5 argumentos: expr, xmin, xmax, ymin, ymax")

        expr = args[0]
        xmin = float(eval(args[1], {"__builtins__": {}}, _SAFE_NAMES))
        xmax = float(eval(args[2], {"__builtins__": {}}, _SAFE_NAMES))
        ymin = float(eval(args[3], {"__builtins__": {}}, _SAFE_NAMES))
        ymax = float(eval(args[4], {"__builtins__": {}}, _SAFE_NAMES))
        opts = {}
        for opt in args[5:]:
            if '=' in opt:
                k, v = opt.split('=',1)
                opts[k.strip()] = v.strip()

        expr_py = expr.replace('^', '**')
        f2 = compile_expr_2d(expr_py)

        # crear malla
        X = np.linspace(xmin, xmax, 120)
        Y = np.linspace(ymin, ymax, 120)
        XX, YY = np.meshgrid(X, Y)
        try:
            Z = f2(XX, YY)
        except Exception as e:
            raise ValueError(f"Error al evaluar expr 3D: {e}")

        # plot surface
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(XX, YY, Z, cmap='viridis')
        ax.set_title(f"z = {expr}")
        png64 = png_from_figure(fig)
        self.ultima_imagen = png64
        self.salida.append(f"draw3d({expr}) generado correctamente.")
        self.actions.append({'type': 'draw3d', 'expr': expr, 'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax})

    # -------------------------
    # compatibilidad: grafica 2d simple (x^2) si no hay expr
    # -------------------------
    def plot_2d_static(self):
        x = np.linspace(-5, 5, 200)
        y = x ** 2
        fig, ax = plt.subplots()
        ax.plot(x, y)
        png64 = png_from_figure(fig)
        self.ultima_imagen = png64
        self.salida.append("Grafica estática (x^2) generada (compatibilidad).")
        self.actions.append({'type': 'draw2d_static'})

# ==========================
# Si se usa directamente:
# ==========================
if __name__ == "__main__":
    sample = """
    win2d ventana;
    draw2d(x^2 + 2*x + 1, -5, 5);
    draw2d(sin(x), -6.28, 6.28, anim=2);
    draw3d(sin(sqrt(x^2 + y^2)), -5, 5, -5, 5);
    """
    it = Interpreter(sample)
    res = it.ejecutar()
    print(res["texto"])
    if res["imagen"]:
        print("Imagen generada (base64 len):", len(res["imagen"]))
