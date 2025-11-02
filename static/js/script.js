// ==========================================
// FRONTEND DEL COMPILADOR WEB (ACTUALIZADO)
// Autor: Dino & ChatGPT
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formCompilador");
  const codeInput = document.getElementById("codigo");
  const outputText = document.getElementById("salidaTexto");
  const outputImage = document.getElementById("salidaImagen");
  const loader = document.getElementById("loader");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const codigo = codeInput.value.trim();
    if (!codigo) {
      alert("Por favor, ingrese código antes de compilar.");
      return;
    }

    // Limpiar resultados previos
    outputText.textContent = "";
    outputImage.innerHTML = "";
    loader.style.display = "block";

    try {
      const formData = new FormData();
      formData.append("codigo", codigo);

      const response = await fetch("/compilar", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      loader.style.display = "none";

      if (data.estado === "error_lexico") {
        outputText.textContent = "❌ Error léxico:\n" + data.errores.join("\n");
        return;
      }

      if (data.estado === "error_sintactico") {
        outputText.textContent = "❌ Error sintáctico:\n" + data.errores.join("\n");
        return;
      }

      if (data.estado === "correcto") {
        outputText.textContent = "✅ Ejecución correcta:\n\n" + data.texto;

        if (data.imagen) {
          // Detectar si es GIF o PNG
          const img = document.createElement("img");
          img.style.maxWidth = "100%";
          img.style.borderRadius = "10px";
          img.style.boxShadow = "0 0 15px rgba(0,0,0,0.3)";
          img.alt = "Resultado gráfico";

          // Heurística simple: si es animación -> suele ser más largo
          if (data.imagen.startsWith("R0lGOD") || data.imagen.length > 200000) {
            img.src = "data:image/gif;base64," + data.imagen;
          } else {
            img.src = "data:image/png;base64," + data.imagen;
          }

          outputImage.appendChild(img);
        }
      } else {
        outputText.textContent = "⚠️ Resultado inesperado:\n" + JSON.stringify(data, null, 2);
      }
    } catch (error) {
      loader.style.display = "none";
      outputText.textContent = "❌ Error en la conexión o ejecución:\n" + error;
    }
  });
});
