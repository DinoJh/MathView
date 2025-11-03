import re
import ast
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para servidor
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from matplotlib.animation import FuncAnimation, PillowWriter

# Configuración de matplotlib para tema oscuro elegante
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

# -------------------------
# Utilidades de evaluación segura
# -------------------------
_SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_NUMPY = {
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
    'abs': np.abs, 'pi': np.pi, 'e': np.e,
    'arctan2': np.arctan2, 'arcsin': np.arcsin,
    'arccos': np.arccos, 'sinh': np.sinh, 'cosh': np.cosh
}
_SAFE_NAMES = {}
_SAFE_NAMES.update(_SAFE_MATH)
_SAFE_NAMES.update(_SAFE_NUMPY)

def compile_expr_1d(expr_src):
    """Crea función f(x) que evalúa expr_src de forma segura."""
    try:
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
            env = {'x': x}
            env.update(_SAFE_NAMES)
            return eval(code, {"__builtins__": {}}, env)
        return f
    except Exception as e:
        raise ValueError(f"Error compilando expresión: {e}")

def compile_expr_2d(expr_src):
    """Crea función f(x,y) que evalúa expr_src."""
    try:
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

# -------------------------
# Parsing de llamadas
# -------------------------
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

# Regex corregido con el nombre del grupo correcto
CALL_RE = re.compile(
    r'(?P<name>\b(?:draw2d|draw3d|win2d|win3d|text|plane2d|plane3d|display|move|vector2d|vector3d)\b)'
    r'\s*\((?P<args>.*?)\)\s*;',
    re.S | re.IGNORECASE
)

def extract_calls_from_source(source):
    """Extrae todas las llamadas de función del código fuente."""
    matches = CALL_RE.finditer(source)
    calls = []
    for m in matches:
        name = m.group('name').lower()  # ✅ CORREGIDO: usar 'name' en lugar de 'n'
        raw = m.group('args').strip()
        args = split_top_level_commas(raw)
        calls.append({'name': name, 'raw': raw, 'args': args})
    return calls

# -------------------------
# Funciones de graficado
# -------------------------
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

# -------------------------
# Interpreter
# -------------------------
class Interpreter:
    def __init__(self, source_code):
        self.source = source_code if isinstance(source_code, str) else ""
        self.variables = {}
        self.salida = []
        self.ultima_imagen = None
        self.tipo_imagen = "png"
        self.actions = []

    def ejecutar(self):
        """Ejecuta el código y retorna resultados."""
        try:
            if not self.source or not self.source.strip():
                self.salida.append("⚠️ Código vacío")
                return self.get_result()

            calls = extract_calls_from_source(self.source)
            
            if not calls:
                self.salida.append("⚠️ No se encontraron instrucciones válidas.")
                self.salida.append("Ejemplo: draw2d(sin(x), -6.28, 6.28);")
                return self.get_result()

            for call in calls:
                self.execute_call(call)

        except Exception as e:
            self.salida.append(f"❌ Error en ejecución: {str(e)}")

        return self.get_result()

    def get_result(self):
        """Retorna el resultado de la ejecución."""
        return {
            "texto": "\n".join(self.salida),
            "imagen": self.ultima_imagen,
            "tipo_imagen": self.tipo_imagen,
            "acciones": self.actions
        }

    def execute_call(self, call):
        """Ejecuta una llamada de función."""
        name = call['name']
        args = call['args']
        
        try:
            if name == 'draw2d':
                self.handle_draw2d(args)
            elif name == 'draw3d':
                self.handle_draw3d(args)
            elif name in ('win2d', 'win3d'):
                self.salida.append(f"✅ Ventana {name} creada")
                self.actions.append({'type': 'window', 'name': name})
            elif name == 'display':
                self.salida.append("✅ Display ejecutado")
            elif name == 'text':
                self.handle_text(args)
            else:
                self.salida.append(f"✅ {name} ejecutado")
        except Exception as e:
            self.salida.append(f"❌ Error en {name}: {str(e)}")

    def handle_draw2d(self, args):
        """Maneja gráficos 2D."""
        if len(args) < 3:
            raise ValueError("draw2d requiere: expresión, xmin, xmax")

        expr = args[0].strip()
        
        # Parsear opciones
        opts = {}
        numeric_args = []
        for arg in args[1:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                opts[k.strip()] = v.strip().strip('"').strip("'")
            else:
                numeric_args.append(arg)

        if len(numeric_args) < 2:
            raise ValueError("draw2d requiere xmin y xmax")

        # Evaluar límites
        try:
            xmin = float(eval(numeric_args[0], {"__builtins__": {}}, _SAFE_NAMES))
            xmax = float(eval(numeric_args[1], {"__builtins__": {}}, _SAFE_NAMES))
            if xmin >= xmax:
                raise ValueError("xmin debe ser menor que xmax")
        except Exception as e:
            raise ValueError(f"Error en límites: {e}")

        # Opciones
        anim_seconds = float(opts.get('anim', 0))
        color = opts.get('color', 'deepskyblue')

        # Compilar expresión
        expr_py = expr.replace('^', '**')
        f = compile_expr_1d(expr_py)

        # Generar datos
        x = np.linspace(xmin, xmax, 800)
        y = f(x)

        # Validar resultados
        if not isinstance(y, np.ndarray) or y.shape != x.shape:
            raise ValueError("La expresión debe devolver valores para cada x")

        # Animación o estático
        if anim_seconds > 0:
            self.create_2d_animation(x, y, expr, anim_seconds, color)
        else:
            self.create_2d_static(x, y, expr, color)

    def create_2d_static(self, x, y, expr, color):
        """Crea gráfico 2D estático."""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, color=color, linewidth=2, label=f'y = {expr}')
        ax.set_title(f'Gráfico 2D: y = {expr}', fontsize=14, fontweight='bold')
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.ultima_imagen = png_from_figure(fig)
        self.tipo_imagen = "png"
        self.salida.append(f"✅ Gráfico 2D: {expr}")
        self.actions.append({'type': 'draw2d', 'expr': expr})

    def create_2d_animation(self, x, y, expr, seconds, color):
        """Crea animación 2D."""
        frames = int(seconds * 20)
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.set_xlim(x.min(), x.max())
        y_min, y_max = np.nanmin(y), np.nanmax(y)
        margin = (y_max - y_min) * 0.1 if (y_max - y_min) != 0 else 1.0
        ax.set_ylim(y_min - margin, y_max + margin)
        ax.set_title(f'Animación: y = {expr}', fontsize=14, fontweight='bold')
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        line, = ax.plot([], [], lw=2, color=color)

        def init():
            line.set_data([], [])
            return (line,)

        def update(frame):
            idx = int(len(x) * (frame + 1) / frames)
            line.set_data(x[:idx], y[:idx])
            return (line,)

        anim = FuncAnimation(fig, update, frames=frames, init_func=init, blit=True)
        
        self.ultima_imagen = gif_from_animation(anim, fps=20)
        self.tipo_imagen = "gif"
        self.salida.append(f"✅ Animación 2D: {expr} ({seconds}s)")
        self.actions.append({'type': 'draw2d_anim', 'expr': expr})

    def handle_draw3d(self, args):
        """Maneja gráficos 3D."""
        if len(args) < 5:
            raise ValueError("draw3d requiere: expresión, xmin, xmax, ymin, ymax")

        expr = args[0].strip()
        
        try:
            xmin = float(eval(args[1], {"__builtins__": {}}, _SAFE_NAMES))
            xmax = float(eval(args[2], {"__builtins__": {}}, _SAFE_NAMES))
            ymin = float(eval(args[3], {"__builtins__": {}}, _SAFE_NAMES))
            ymax = float(eval(args[4], {"__builtins__": {}}, _SAFE_NAMES))
        except Exception as e:
            raise ValueError(f"Error en límites 3D: {e}")

        # Compilar expresión 2D
        expr_py = expr.replace('^', '**')
        f2 = compile_expr_2d(expr_py)

        # Crear malla
        X = np.linspace(xmin, xmax, 100)
        Y = np.linspace(ymin, ymax, 100)
        XX, YY = np.meshgrid(X, Y)
        
        try:
            Z = f2(XX, YY)
        except Exception as e:
            raise ValueError(f"Error evaluando expresión 3D: {e}")

        # Graficar
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
        self.salida.append(f"✅ Gráfico 3D: {expr}")
        self.actions.append({'type': 'draw3d', 'expr': expr})

    def handle_text(self, args):
        """Maneja texto."""
        if args:
            texto = args[0].strip('"').strip("'")
            self.salida.append(f"📝 {texto}")