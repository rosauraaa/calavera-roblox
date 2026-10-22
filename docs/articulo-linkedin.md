# Calavera Blox: una máscara de Día de Muertos pintada sobre la malla de tu cara

**Objetivo:**  
Esta actividad pedía mejorar el filtro facial anterior con una máscara inspirada en el Día de Muertos que se ajuste con precisión a ojos, nariz, boca y contorno, y que se deforme con los gestos sin desprenderse. Mi propuesta es Calavera Blox: una calavera de azúcar con cempasúchil, papel picado y una nariz de corazón, que se vuelve parte de tu cara.

**Herramientas:**
MediaPipe Face Landmarker para la malla facial y los gestos.
Blender para exportar la plantilla UV y revisar la textura sobre la malla.
Python con Pillow para pintar la textura.
three.js para el render.
Web Audio API para los sonidos.

**Proceso:**
Tomé el modelo canónico de MediaPipe, que trae su mapa UV, y exporté la plantilla desde el UV Editor de Blender.
Descubrí que el OBJ usa índices distintos para vértices y UV, así que escribí un script que deja una UV por landmark.
Pinté la máscara sobre la plantilla, colocando cada adorno en la posición UV de landmarks reales: el contorno de los ojos para las cuencas, los labios para la boca cosida y la frente para la flor. Así el diseño cae justo donde debe.
Dejé transparentes los ojos y la boca interior, para que se vean tus ojos y tu boca reales.

**Interactividad:** 
Al abrir la boca cae una lluvia de pétalos de cempasúchil con un arpegio de marimba. Al subir las cejas la calavera cambia de paleta (clásica, turquesa o dorada) y aparece un arco de velas encendidas alrededor de la cabeza.

**Retos:**
Cuidar el tema con respeto: investigué los elementos tradicionales (calavera de azúcar, cempasúchil, papel picado, velas) y los usé como homenaje, no como disfraz de terror.
Precisión: cualquier error de UV se nota de inmediato en la cámara. Revisé la textura en Blender sobre la malla antes de probarla en vivo.
Lectura en cámara: el detalle fino se pierde, así que usé colores saturados, contornos gruesos y diseño simétrico.

**Resultado:** 
Una máscara que se mantiene alineada en ojos, nariz, boca y contorno, se deforma con cada gesto y tiene efectos temáticos. Funciona en el navegador del teléfono sin instalar nada.

Pruébala: https://rosauraaa.github.io/calavera-roblox/

Repositorio: https://github.com/rosauraaa/calavera-roblox

#DíaDeMuertos #RealidadAumentada #MediaPipe #Blender #threejs #WebAR
