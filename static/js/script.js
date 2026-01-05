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

// ===== EJEMPLOS =====

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

// ===== EVENT LISTENERS =====

btnCompilar.addEventListener('click', () => compilar(true));
btnLimpiar.addEventListener('click', limpiar);
btnClearConsole.addEventListener('click', limpiarSoloConsola);

// Menú de ejemplos
btnEjemplos.addEventListener('click', (e) => {
    e.stopPropagation();
    ejemplosDropdown.classList.toggle('show');
});

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
    
    // Tab para indentación
    if (e.key === 'Tab') {
        e.preventDefault();
        const start = codigoTextarea.selectionStart;
        const end = codigoTextarea.selectionEnd;
        const value = codigoTextarea.value;
        
        codigoTextarea.value = value.substring(0, start) + '    ' + value.substring(end);
        codigoTextarea.selectionStart = codigoTextarea.selectionEnd = start + 4;
    }
});

// Actualizar contador de líneas
codigoTextarea.addEventListener('input', actualizarLineCount);

function actualizarLineCount() {
    const lines = codigoTextarea.value.split('\n').length;
    lineCount.textContent = `Líneas: ${lines}`;
}

// ===== FUNCIONES DE COMPILACIÓN =====

function compilar(esNuevaCompilacion = false) {
    const codigo = codigoTextarea.value.trim();
    
    if (!codigo) {
        mostrarEstado('error', 'Por favor, escribe código antes de compilar');
        return;
    }
    
    if (esNuevaCompilacion) {
        userInputs = [];
        codigoActual = codigo;
        salidaPreviaGuardada = [];
        limpiarSoloConsola();
        // ARREGLO: Ocultar visualización al iniciar nueva compilación
        visualizacion.classList.add('oculto');
    }
    
    mostrarEstado('advertencia', '⏳ Compilando...');
    btnCompilar.disabled = true;
    
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
    if (data.tokens && userInputs.length === 0) {
        mostrarTokens(data.tokens);
    }
    
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
                if (data.solicitudes[0].salida_previa) {
                    salidaPreviaGuardada = data.solicitudes[0].salida_previa;
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
            mostrarEstado('error', '❌ Error');
            if (data.errores) {
                mostrarErrores(data.errores);
            } else if (data.mensaje) {
                agregarLineaConsola(data.mensaje, 'error');
            }
            esperandoInput = false;
            break;
    }
}

function mostrarSalida(data) {
    if (data.salida) {
        const lineas = data.salida.split('\n');
        lineas.forEach(linea => {
            if (linea.trim()) {
                agregarLineaConsola(linea, 'salida');
            }
        });
    }
    
    if (data.errores && data.errores.length > 0) {
        data.errores.forEach(error => {
            agregarLineaConsola(error, 'error');
        });
    }
    
    // ARREGLO: Solo mostrar imagen si existe, sino ocultarla
    if (data.imagen) {
        mostrarImagen(data.imagen);
    } else {
        visualizacion.classList.add('oculto');
    }
}

function mostrarSalidaPrevia(lineas) {
    lineas.forEach(linea => {
        if (linea.trim()) {
            agregarLineaConsola(linea, 'salida');
        }
    });
}

function solicitarInput(solicitud) {
    agregarLineaConsola(solicitud.mensaje, 'prompt');
    consolaInput.classList.remove('oculto');
    inputValor.focus();
}

function enviarInput() {
    const valor = inputValor.value.trim();
    
    if (!valor) {
        return;
    }
    
    agregarLineaConsola(`> ${valor}`, 'input');
    userInputs.push(valor);
    inputValor.value = '';
    consolaInput.classList.add('oculto');
    esperandoInput = false;
    
    compilar(false);
}

function mostrarErrores(errores) {
    errores.forEach(error => {
        agregarLineaConsola(error, 'error');
    });
}

function mostrarImagen(imagenBase64) {
    visualizacion.classList.remove('oculto');
    grafico.src = `data:image/png;base64,${imagenBase64}`;
}

function agregarLineaConsola(texto, tipo = 'salida') {
    const placeholder = consola.querySelector('.consola-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const linea = document.createElement('div');
    linea.className = `linea-consola ${tipo}`;
    linea.textContent = texto;
    consola.appendChild(linea);
    consola.scrollTop = consola.scrollHeight;
}

function mostrarTokens(tokens) {
    tokensOutput.innerHTML = '';
    tokenCount.textContent = `${tokens.length} tokens`;
    
    tokens.forEach(([lexema, tipo], index) => {
        const tokenItem = document.createElement('div');
        tokenItem.className = 'token-item';
        
        // Asignar clase según tipo
        if (tipo.includes('KEYWORD') || tipo.includes('CONDICIONAL') || tipo.includes('BUCLE')) {
            tokenItem.classList.add('keyword');
        } else if (tipo.includes('FUNCION')) {
            tokenItem.classList.add('function');
        } else if (tipo.includes('TIPO')) {
            tokenItem.classList.add('type');
        } else if (tipo === 'NUMERO') {
            tokenItem.classList.add('number');
        } else if (tipo === 'CADENA') {
            tokenItem.classList.add('string');
        } else if (tipo === 'IDENTIFICADOR') {
            tokenItem.classList.add('identifier');
        } else {
            tokenItem.classList.add('operator');
        }
        
        tokenItem.innerHTML = `
            <span class="token-lexema">${lexema}</span>
            <span class="token-tipo">${tipo}</span>
        `;
        
        tokensOutput.appendChild(tokenItem);
    });
}

function mostrarEstado(tipo, mensaje) {
    estadoBar.className = `estado-bar ${tipo}`;
    estadoBar.classList.remove('oculto');
    
    const iconos = {
        'correcto': '✅',
        'error': '❌',
        'advertencia': '⚠️'
    };
    
    estadoIcono.textContent = iconos[tipo] || '';
    estadoTexto.textContent = mensaje;
    
    setTimeout(() => {
        if (tipo !== 'error' && tipo !== 'advertencia') {
            estadoBar.classList.add('oculto');
        }
    }, 5000);
}

function limpiarSoloConsola() {
    consola.innerHTML = `
        <div class="consola-placeholder">
            <div class="placeholder-icon">💡</div>
            <div class="placeholder-text">La salida de tu programa aparecerá aquí</div>
            <div class="placeholder-hint">Escribe código y presiona "Compilar" o Ctrl+Enter</div>
        </div>
    `;
    // ARREGLO: Ocultar visualización al limpiar consola
    visualizacion.classList.add('oculto');
}

function limpiar() {
    codigoTextarea.value = '';
    limpiarSoloConsola();
    visualizacion.classList.add('oculto');
    tokensOutput.innerHTML = `
        <div class="tokens-placeholder">
            <div class="placeholder-icon">🔤</div>
            <div class="placeholder-text">Los tokens aparecerán aquí</div>
        </div>
    `;
    tokenCount.textContent = '0 tokens';
    estadoBar.classList.add('oculto');
    consolaInput.classList.add('oculto');
    userInputs = [];
    esperandoInput = false;
    actualizarLineCount();
}
