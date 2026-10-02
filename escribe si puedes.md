*Estudiantes:* Diego Guadalupe Torres Bravo y Christopher Emmanuel Jimenez Cuevas.

# Escribe si puedes

## Problema o necesidad

Muchas personas, en especial estudiantes y escritores, tienen dificultad para mantener un flujo continuo de escritura debido a malos hábitos como la procrastinación, el perfeccionismo paralizante y la autoedición constante que interrumpe el proceso creativo. 

Hoy en día, las herramientas de escritura convencionales (como procesadores de texto o blocs de notas) no incluyen ningún mecanismo que incentive la continuidad ni evalúe la concentración activa: el usuario puede dejar el texto detenido indefinidamente o escribir caracteres aleatorios sin ninguna consecuencia, lo cual disminuye el hábito de estimulación de la escritura y reduce la producción genuina de ideas.

---

## Usuario objetivo

Estudiantes universitarios, investigadores, escritores, redactores o cualquier persona que requiera entrenar la escritura libre, estructuración ágil de ideas, fluidez textual y sesiones de trabajo de alta concentración sin distracciones.

---

## Funcionamiento y Dinámica

El programa combina una **mecánica de juego (*gamificación*)** con la **técnica de productividad Pomodoro** y una **asistencia inteligente de validación en tiempo real**:

1. **Monitoreo de Continuidad e Inactividad:**
   El programa monitorea de forma continua el tiempo transcurrido desde la última acción de escritura válida. Si se detecta una pausa, la pantalla comienza a cubrirse progresivamente de color rojo o blanco (indicador de peligro). Si el usuario retoma la escritura a tiempo, el nivel de alerta se disipa. Si la inactividad supera el umbral configurado, la pantalla se cubre por completo, se penaliza al usuario y el texto del nivel actual se borra.

2. **Integración con Metodología Pomodoro:**
   La sesión de escritura se organiza en bloques de trabajo estructurados:
   - **Bloque de Escritura Activa:** Intervalo de concentración profunda (ej. 15, 20 o 25 minutos según el nivel) donde el temporizador avanza y la regla de no-inactividad se mantiene activa.
   - **Bloque de Descanso Seguro:** Al superar el tiempo de trabajo, el temporizador de alerta se desactiva y el usuario entra en una pausa segura de descanso antes de continuar al siguiente ciclo o nivel.

3. **Sistema de Niveles Progresivos (Modo Juego):**
   El usuario avanza a través de niveles de dificultad creciente:
   - **Nivel 1 (Calentamiento):** Umbral de tolerancia a pausas más flexible (ej. 7-8 segundos) y meta de palabras moderada.
   - **Nivel 2 (Enfoque / Fluidez):** Umbral de pausa estándar (ej. 4-5 segundos) y requisito de mayor consistencia.
   - **Nivel 3 (Modo Máximo Desafío):** Umbral estricto (ej. 2-3 segundos), mayor exigencia de longitud y análisis de coherencia riguroso.

4. **Asistencia Inteligente (Filtro Antifraude y Coherencia Semántica):**
   Para evitar que el usuario supere los niveles tecleando caracteres al azar (*keyboard mash* como `"asdfghjkl"`, palabras incoherentes o repeticiones infinitas), el sistema cuenta con un módulo de **Asistencia Inteligente**:
   - **Detección de texto basura (*Gibberish Detection*):** Evalúa patrones lingüísticos, existencia de palabras reales y estructura gramatical básica.
   - **Validación de Continuidad y Coherencia Lógica:** Revisa que las oraciones agregadas tengan sentido contextual y conexión lógica con el tema desarrollado.
   - Si se detecta escritura incoherente o aleatoria, el texto inválido **no cuenta para el avance del nivel** y se activa una advertencia que acelera la alerta de inactividad.

5. **Calificación Final y Reporte de Desempeño:**
   Al finalizar cada sesión o nivel completado, el sistema genera una **calificación final estructurada** (ej. 0 a 100 o escala de estrellas) basada en:
   - **Velocidad neta de escritura:** Palabras por minuto (WPM) válidas.
   - **Índice de Fluidez:** Cantidad de pausas críticas evitadas.
   - **Calidad y Coherencia:** Puntuación otorgada por el motor de asistencia inteligente.
   - **Cumplimiento del Pomodoro:** Nivel alcanzado y consistencia temporal.

---

## Responsabilidades del programa

- **Control de Tiempo e Inactividad:** Detectar pausas y calcular la progresión visual del nivel de alerta.
- **Gestión de Ciclos Pomodoro:** Administrar estados de trabajo activo, descansos y transiciones de tiempo.
- **Lógica de Niveles y Gamificación:** Determinar las metas de palabras, umbrales de penalización y condiciones de victoria/derrota de cada nivel.
- **Asistencia Inteligente de Contenido:** Analizar y validar que el texto ingresado sea coherente, estructurado y no generado por pulsaciones aleatorias.
- **Motor de Calificación Final:** Calcular métricas de rendimiento y emitir el reporte final de la sesión.
- **Acción Punitiva/Reinicio:** Ejecutar el borrado seguro y reinicio del nivel cuando se incumpla la regla de continuidad.

---

## Información necesaria (Entradas y Estado)

- **Marca de tiempo (*timestamp*):** Registro temporal de cada tecla presionada válida.
- **Buffer de texto:** Contenido del texto escrito en el nivel actual y acumulado en la sesión.
- **Parámetros del Nivel Actual:** Umbral de inactividad, meta de palabras/tiempo y multiplicador de dificultad.
- **Estado del Ciclo Pomodoro:** Minutos transcurridos de trabajo y estado de pausa/descanso.
- **Historial de métricas:** Total de palabras válidas, palabras descartadas por incoherencia, pausas registradas y tiempo total de concentración.

---

## Resultado esperado

El programa transforma la escritura en una experiencia desafiante y enfocada, permitiendo al usuario:
1. Eliminar bloqueos creativos y procrastinación mediante la urgencia controlada.
2. Producir textos coherentes y de valor, respaldados por la validación inteligente.
3. Mantener hábitos de concentración sostenibles gracias a los ciclos Pomodoro.
4. Medir su progreso y evolución a través del sistema de niveles y calificaciones finales.

---

## Valor de la propuesta

A diferencia de editores tradicionales o simples cronómetros, **Escribe si puedes** integra la presión positiva de un videojuego (*gamificación*), la disciplina de la técnica Pomodoro y la garantía de calidad mediante inteligencia artificial. Es una herramienta integral para el entrenamiento de la disciplina mental, la improvisación escrita y la redacción productiva.
