document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('formCompilador');
    const codigoTextarea = document.getElementById('codigo');
    const loader = document.getElementById('loader');
    const salidaTexto = document.getElementById('salidaTexto');
    const salidaImagen = document.getElementById('salidaImagen');

    // Ejemplo por defecto
    const ejemploPorDefecto = `// Ejemplo de gráficos 2D y 3D 

// Ejemplo por defecto:
draw3d(x*x + y*y, 0, 15, 0, 15);`;

    if (codigoTextarea.value.trim() === '') {
        codigoTextarea.value = ejemploPorDefecto;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const codigo = codigoTextarea.value;

        if (!codigo.trim()) {
            mostrarError('Por favor escribe código antes de ejecutar');
            return;
        }

        // Limpiar salida anterior
        salidaTexto.textContent = '';
        salidaImagen.innerHTML = '';
        loader.style.display = 'block';

        try {
            const response = await fetch('/compilar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ codigo: codigo })
            });

            const data = await response.json();

            loader.style.display = 'none';

            if (data.estado === 'correcto') {
                mostrarResultadoCorrecto(data);
            } else if (data.estado === 'error_lexico') {
                mostrarErrorLexico(data);
            } else if (data.estado === 'error_sintactico') {
                mostrarErrorSintactico(data);
            } else {
                mostrarError(data.mensaje || 'Error desconocido', data.errores);
            }

        } catch (error) {
            loader.style.display = 'none';
            mostrarError('Error de conexión: ' + error.message);
        }
    });

    function mostrarResultadoCorrecto(data) {
        let textoSalida = '✅ EJECUCIÓN EXITOSA\n\n';
        textoSalida += data.texto || 'Sin salida de texto';
        
        if (data.acciones && data.acciones.length > 0) {
            textoSalida += '\n\n📋 Acciones realizadas:\n';
            data.acciones.forEach((accion, i) => {
                textoSalida += `  ${i + 1}. ${accion.type}`;
                if (accion.expr) textoSalida += `: ${accion.expr}`;
                textoSalida += '\n';
            });
        }

        salidaTexto.textContent = textoSalida;
        salidaTexto.style.color = '#00ff88';

        // Mostrar imagen si existe
        if (data.imagen) {
            const tipoImagen = data.tipo_imagen || 'png';
            const mimeType = tipoImagen === 'gif' ? 'image/gif' : 'image/png';
            const img = document.createElement('img');
            img.src = `data:${mimeType};base64,${data.imagen}`;
            img.alt = 'Gráfico generado';
            img.style.maxWidth = '100%';
            img.style.borderRadius = '8px';
            img.style.marginTop = '10px';
            salidaImagen.appendChild(img);
        }
    }

    function mostrarErrorLexico(data) {
        let textoError = '❌ ERRORES LÉXICOS\n\n';
        if (data.errores && data.errores.length > 0) {
            data.errores.forEach(error => {
                textoError += `• ${error}\n`;
            });
        }
        textoError += '\n📝 Tokens reconocidos:\n';
        if (data.tokens && data.tokens.length > 0) {
            data.tokens.slice(0, 20).forEach(token => {
                textoError += `  ${token[0]} → ${token[1]}\n`;
            });
            if (data.tokens.length > 20) {
                textoError += `  ... y ${data.tokens.length - 20} más\n`;
            }
        }
        salidaTexto.textContent = textoError;
        salidaTexto.style.color = '#ff4444';
    }

    function mostrarErrorSintactico(data) {
        let textoError = '❌ ERRORES SINTÁCTICOS\n\n';
        if (data.errores && data.errores.length > 0) {
            data.errores.forEach(error => {
                textoError += `• ${error}\n`;
            });
        }
        salidaTexto.textContent = textoError;
        salidaTexto.style.color = '#ff8844';
    }

    function mostrarError(mensaje, errores) {
        let textoError = `❌ ERROR\n\n${mensaje}\n`;
        if (errores && Array.isArray(errores)) {
            textoError += '\nDetalles:\n';
            errores.forEach(e => {
                textoError += `• ${e}\n`;
            });
        }
        salidaTexto.textContent = textoError;
        salidaTexto.style.color = '#ff4444';
    }

    // Atajos de teclado
    codigoTextarea.addEventListener('keydown', function(e) {
        // Tab para insertar espacios
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 4;
        }
        
        // Ctrl+Enter para ejecutar
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
});