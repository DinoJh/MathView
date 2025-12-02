// Variables globales
let userInputs = [];
let esperandoInput = false;
let codigoActual = '';

// Elementos del DOM
const codigoTextarea = document.getElementById('codigo');
const btnCompilar = document.getElementById('btn-compilar');
const btnLimpiar = document.getElementById('btn-limpiar');
const consola = document.getElementById('consola');
const consolaInput = document.getElementById('consola-input');
const inputPrompt = document.getElementById('input-prompt');
const inputValor = document.getElementById('input-valor');
const estadoBar = document.getElementById('estado-bar');
const estadoIcono = document.getElementById('estado-icono');
const estadoTexto = document.getElementById('estado-texto');
const visualizacion = document.getElementById('visualizacion');
const grafico = document.getElementById('grafico');
const tokensOutput = document.getElementById('tokens-output');

// Event Listeners
btnCompilar.addEventListener('click', () => compilar(true));
btnLimpiar.addEventListener('click', limpiar);

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
        limpiarConsola();
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
    inputPrompt.textContent = solicitud.mensaje;
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
    agregarLineaConsola(`${inputPrompt.textContent} ${valor}`, 'input');
    
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

function limpiarConsola() {
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
    
    // Limpiar placeholder si existe
    const placeholder = tokensOutput.querySelector('.tokens-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    tokens.forEach(([lexema, tipo]) => {
        const tokenItem = document.createElement('div');
        tokenItem.className = 'token-item';
        tokenItem.innerHTML = `<strong>${tipo}</strong>: ${lexema}`;
        tokensOutput.appendChild(tokenItem);
    });
}

function limpiar() {
    codigoTextarea.value = '';
    limpiarConsola();
    estadoBar.classList.add('oculto');
    visualizacion.classList.add('oculto');
    tokensOutput.innerHTML = '<div class="tokens-placeholder">Los tokens aparecerán aquí después de compilar...</div>';
    userInputs = [];
    codigoActual = '';
    esperandoInput = false;
}

// Código inicial de ejemplo
window.addEventListener('DOMContentLoaded', () => {
    if (!codigoTextarea.value) {
        codigoTextarea.value = `int n = 10;
pri("Hola Mundo");
pri(n);`;
    }
});