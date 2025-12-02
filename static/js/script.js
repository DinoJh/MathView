// Variables globales
let userInputs = [];
let esperandoInput = false;
let codigoActual = '';
let salidaPreviaGuardada = [];

// Elementos del DOM
const codigoTextarea = document.getElementById('codigo');
const btnCompilar = document.getElementById('btn-compilar');
const btnLimpiar = document.getElementById('btn-limpiar');
const btnEjemplos = document.getElementById('btn-ejemplos');
const ejemplosDropdown = document.getElementById('ejemplos-dropdown');
const consola = document.getElementById('consola');
const btnClearConsole = document.getElementById('btn-clear-console');
const consolaInput = document.getElementById('consola-input');
const inputValor = document.getElementById('input-valor');
const estadoBar = document.getElementById('estado-bar');
const estadoIcono = document.getElementById('estado-icono');
const estadoTexto = document.getElementById('estado-texto');
const visualizacion = document.getElementById('visualizacion');
const grafico = document.getElementById('grafico');
const tokensOutput = document.getElementById('tokens-output');
const tokenCount = document.getElementById('token-count');
const lineCount = document.getElementById('line-count');

// Ejemplos predefinidos
const ejemplos = {
    basico: `int n = 10;
pri("Hola Mundo");
pri(n);`,
    
    condicional: `int edad = 20;

if(edad >= 18) {
    pri("Eres mayor de edad");
} else {
    pri("Eres menor de edad");
}`,
    
    bucle: `int i = 1;

pri("Contando del 1 al 5:");
while(i <= 5) {
    pri(i);
    i++;
}
pri("Fin del conteo");`,
    
    input: `int numero;

pri("Ingrese un numero:");
put(numero);

if(numero % 2 == 0) {
    pri("El numero es par");
} else {
    pri("El numero es impar");
}`,
    
    grafico2d: `pri("Generando grafico 2D...");
draw2d(sin(x), -6.28, 6.28);
pri("Grafico completado");`,
    
    grafico3d: `pri("Generando grafico 3D...");
draw3d(x^2 + y^2, -5, 5, -5, 5);
pri("Superficie completada");`,
    
    menu: `int opcion;

pri("=== GRAFICADOR ===");
pri("1. Seno 2D");
pri("2. Paraboloide 3D");
pri("3. Coseno 2D");
pri("");
pri("Seleccione opcion:");
put(opcion);

if(opcion == 1) {
    pri("Grafico de seno");
    draw2d(sin(x), -6.28, 6.28);
} elif(opcion == 2) {
    pri("Paraboloide 3D");
    draw3d(x^2 + y^2, -5, 5, -5, 5);
} elif(opcion == 3) {
    pri("Grafico de coseno");
    draw2d(cos(x), -6.28, 6.28);
} else {
    pri("Opcion invalida");
}`,
    
    avanzado: `int n = 10;
int i = 1;
int suma = 0;

pri("Calculando suma de 1 a 10:");

while(i <= n) {
    suma = suma + i;
    i++;
}

pri("La suma es:");
pri(suma);

if(suma > 50) {
    pri("La suma es mayor a 50");
    draw2d(x^2, -5, 5);
} else {
    pri("La suma es menor o igual a 50");
}`
};

// Event Listeners
btnCompilar.addEventListener('click', () => compilar(true));
btnLimpiar.addEventListener('click', limpiar);
btnClearConsole.addEventListener('click', limpiarSoloConsola);

// Menú de ejemplos
btnEjemplos.addEventListener('click', (e) => {
    e.stopPropagation();
    ejemplosDropdown.classList.toggle('show');
});

// Cerrar dropdown al hacer click fuera
document.addEventListener('click', (e) => {
    if (!e.target.closest('.ejemplos-menu')) {
        ejemplosDropdown.classList.remove('show');
    }
});

// Cargar ejemplos
document.querySelectorAll('.ejemplo-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const ejemplo = btn.dataset.ejemplo;
        codigoTextarea.value = ejemplos[ejemplo];
        ejemplosDropdown.classList.remove('show');
        actualizarLineCount();
    });
});

// Enter en el input de consola
inputValor.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        enviarInput();
    }
});

// Atajo de teclado Ctrl+Enter para compilar
codigoTextarea.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        compilar(true);
    }
});

// Actualizar contador de líneas
codigoTextarea.addEventListener('input', actualizarLineCount);

function actualizarLineCount() {
    const lines = codigoTextarea.value.split('\n').length;
    lineCount.textContent = `Líneas: ${lines}`;
}

function compilar(esNuevaCompilacion = false) {
    const codigo = codigoTextarea.value.trim();
    
    if (!codigo) {
        mostrarEstado('error', 'Por favor, escribe código antes de compilar');
        return;
    }
    
    // Si es una nueva compilación, resetear inputs
    if (esNuevaCompilacion) {
        userInputs = [];
        codigoActual = codigo;
        salidaPreviaGuardada = [];
        limpiarSoloConsola();
    }
    
    // Mostrar estado de compilación
    mostrarEstado('advertencia', '⏳ Compilando...');
    btnCompilar.disabled = true;
    
    // Enviar petición
    fetch('/compilar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            codigo: codigoActual,
            inputs: userInputs
        })
    })
    .then(response => response.json())
    .then(data => {
        procesarRespuesta(data);
        btnCompilar.disabled = false;
    })
    .catch(error => {
        mostrarEstado('error', `❌ Error de conexión: ${error.message}`);
        agregarLineaConsola(`Error: ${error.message}`, 'error');
        btnCompilar.disabled = false;
        esperandoInput = false;
    });
}

function procesarRespuesta(data) {
    // Mostrar tokens solo en primera compilación
    if (data.tokens && userInputs.length === 0) {
        mostrarTokens(data.tokens);
    }
    
    // Manejar diferentes estados
    switch(data.estado) {
        case 'correcto':
            mostrarEstado('correcto', '✅ Compilación exitosa');
            mostrarSalida(data);
            esperandoInput = false;
            break;
            
        case 'con_errores':
            mostrarEstado('advertencia', '⚠️ Compilación con errores');
            mostrarSalida(data);
            esperandoInput = false;
            break;
            
        case 'necesita_input':
            if (!esperandoInput) {
                esperandoInput = true;
                // Guardar la salida previa antes de solicitar input
                if (data.solicitudes[0].salida_previa) {
                    salidaPreviaGuardada = data.solicitudes[0].salida_previa;
                    // Mostrar la salida previa
                    mostrarSalidaPrevia(salidaPreviaGuardada);
                }
                solicitarInput(data.solicitudes[0]);
            }
            break;
            
        case 'error_lexico':
            mostrarEstado('error', '❌ Errores léxicos');
            mostrarErrores(data.errores);
            esperandoInput = false;
            break;
            
        case 'error_sintactico':
            mostrarEstado('error', '❌ Errores sintácticos');
            mostrarErrores(data.errores);
            esperandoInput = false;
            break;
            
        case 'error':
            mostrarEstado('error', `❌ ${data.mensaje}`);
            agregarLineaConsola(data.mensaje, 'error');
            if (data.traceback) {
                console.error(data.traceback);
            }
            esperandoInput = false;
            break;
    }
}

function mostrarSalidaPrevia(salida) {
    // Limpiar consola y mostrar salida previa
    limpiarSoloConsola();
    salida.forEach(linea => {
        if (linea.trim()) {
            agregarLineaConsola(linea, 'output');
        }
    });
}

function mostrarSalida(data) {
    // Mostrar salida del programa
    if (data.salida) {
        const lineas = data.salida.split('\n');
        lineas.forEach(linea => {
            if (linea.trim()) {
                agregarLineaConsola(linea, 'output');
            }
        });
    }
    
    // Mostrar errores si hay
    if (data.errores && data.errores.length > 0) {
        data.errores.forEach(error => {
            agregarLineaConsola(error, 'error');
        });
    }
    
    // Mostrar imagen si hay
    if (data.imagen) {
        visualizacion.classList.remove('oculto');
        grafico.src = `data:image/png;base64,${data.imagen}`;
    } else {
        visualizacion.classList.add('oculto');
    }
}

function mostrarErrores(errores) {
    errores.forEach(error => {
        agregarLineaConsola(error, 'error');
    });
}

function solicitarInput(solicitud) {
    // Usar el mensaje personalizado (último pri())
    const mensaje = solicitud.mensaje || `${solicitud.variable}: `;
    agregarLineaConsola(mensaje, 'output');
    
    inputValor.value = '';
    consolaInput.classList.remove('oculto');
    inputValor.focus();
}

function enviarInput() {
    const valor = inputValor.value.trim();
    
    if (!valor) {
        return;
    }
    
    // Mostrar lo que se ingresó
    agregarLineaConsola(`▶ ${valor}`, 'input');
    
    // Guardar el input
    userInputs.push(valor);
    
    // Ocultar el input
    consolaInput.classList.add('oculto');
    inputValor.value = '';
    
    // Recompilar con el nuevo input (NO es nueva compilación)
    setTimeout(() => {
        esperandoInput = false;
        compilar(false);
    }, 100);
}

function agregarLineaConsola(texto, tipo = 'output') {
    // Limpiar placeholder si existe
    const placeholder = consola.querySelector('.consola-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const linea = document.createElement('div');
    linea.className = `consola-line ${tipo}`;
    linea.textContent = texto;
    consola.appendChild(linea);
    consola.scrollTop = consola.scrollHeight;
}

function limpiarSoloConsola() {
    consola.innerHTML = '';
    consolaInput.classList.add('oculto');
}

function mostrarEstado(tipo, mensaje) {
    estadoBar.className = `estado-bar ${tipo}`;
    
    const iconos = {
        'correcto': '✅',
        'error': '❌',
        'advertencia': '⚠️'
    };
    
    estadoIcono.textContent = iconos[tipo] || '📋';
    estadoTexto.textContent = mensaje;
    estadoBar.classList.remove('oculto');
}

function mostrarTokens(tokens) {
    tokensOutput.innerHTML = '';
    
    tokens.forEach(([lexema, tipo]) => {
        const tokenItem = document.createElement('div');
        tokenItem.className = 'token-item';
        tokenItem.innerHTML = `<strong>${tipo}</strong>: ${lexema}`;
        tokensOutput.appendChild(tokenItem);
    });
    
    tokenCount.textContent = `${tokens.length} tokens`;
}

function limpiar() {
    codigoTextarea.value = '';
    limpiarSoloConsola();
    estadoBar.classList.add('oculto');
    visualizacion.classList.add('oculto');
    tokensOutput.innerHTML = '<div class="tokens-placeholder"><div class="placeholder-icon">🔤</div><div class="placeholder-text">Los tokens aparecerán aquí</div></div>';
    tokenCount.textContent = '0 tokens';
    userInputs = [];
    codigoActual = '';
    salidaPreviaGuardada = [];
    esperandoInput = false;
    actualizarLineCount();
}

// Código inicial de ejemplo
window.addEventListener('DOMContentLoaded', () => {
    if (!codigoTextarea.value) {
        codigoTextarea.value = ejemplos.basico;
    }
    actualizarLineCount();
});