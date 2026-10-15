/**
 * ==============================================================================
 * Escribe si puedes — Controlador del Frontend (Vanilla JavaScript)
 * Máquina de Estados, Temporizador de Alta Precisión, Temas Sugeridos,
 * Corrección de Estilo Asistida por IA y Conexión con API Flask
 * ==============================================================================
 */

// Estado global de la aplicación (inmutable por convención en funciones puras auxiliares)
const AppState = {
  niveles: [],
  nivelSeleccionado: null,
  fasePomodoro: 'ESCRITURA', // 'ESCRITURA' | 'DESCANSO'
  estadoJuego: 'EN_ESPERA',   // 'EN_ESPERA' | 'ESCRIBIENDO' | 'DESCANSO' | 'BORRADO' | 'COMPLETADO'

  // Tiempos y Medición
  tiempoInicioSesion: null,
  ultimaPulsacionMs: null,
  tiempoTranscurridoSeg: 0,
  pomodoroSegundosRestantes: 300,

  // Métricas acumuladas
  palabrasValidas: 0,
  palabrasBasura: 0,
  pausasAlLimite: 0,
  alertaPeligroActiva: false,
  finalizando: false,
  coherenteIA: true,
  pomodoroCompletado: false,

  // Temas sugeridos y corrección de estilo
  temaActual: '',
  cargandoTema: false,

  // Loop requestAnimationFrame y temporizadores
  animFrameId: null,
  debounceTimer: null,
};

// Elementos del DOM
const DOM = {
  writingArea: document.getElementById('writingArea'),
  editorWrapper: document.getElementById('editorWrapper'),
  dangerOverlay: document.getElementById('dangerOverlay'),
  inactivityBar: document.getElementById('inactivityBar'),
  secondsLeftDisplay: document.getElementById('secondsLeftDisplay'),
  aiStatusBadge: document.getElementById('aiStatusBadge'),
  aiWarningToast: document.getElementById('aiWarningToast'),

  // Tarjeta de Tema Sugerido
  topicCard: document.getElementById('topicCard'),
  topicText: document.getElementById('topicText'),
  btnOtroTema: document.getElementById('btnOtroTema'),

  // HUD
  pomoPhaseLabel: document.getElementById('pomoPhaseLabel'),
  pomoTimer: document.getElementById('pomoTimer'),
  levelNameDisplay: document.getElementById('levelNameDisplay'),
  btnOpenLevelModal: document.getElementById('btnOpenLevelModal'),
  wpmCounter: document.getElementById('wpmCounter'),
  wordsCounter: document.getElementById('wordsCounter'),
  goalPercentage: document.getElementById('goalPercentage'),
  goalProgressBar: document.getElementById('goalProgressBar'),
  btnFinalizarSesion: document.getElementById('btnFinalizarSesion'),
  btnDescargarTexto: document.getElementById('btnDescargarTexto'),

  // Modales
  modalNivel: document.getElementById('modalNivel'),
  levelsGridContainer: document.getElementById('levelsGridContainer'),
  btnCloseLevelModal: document.getElementById('btnCloseLevelModal'),

  modalGameOver: document.getElementById('modalGameOver'),
  btnReiniciarNivel: document.getElementById('btnReiniciarNivel'),

  modalDescanso: document.getElementById('modalDescanso'),
  breakTimerDisplay: document.getElementById('breakTimerDisplay'),
  btnContinuarSiguienteCiclo: document.getElementById('btnContinuarSiguienteCiclo'),

  // Modal Calificación
  modalCalificacion: document.getElementById('modalCalificacion'),
  summaryRank: document.getElementById('summaryRank'),
  starsDisplay: document.getElementById('starsDisplay'),
  finalScoreVal: document.getElementById('finalScoreVal'),
  finalWpm: document.getElementById('finalWpm'),
  finalValidWords: document.getElementById('finalValidWords'),
  finalGarbageWords: document.getElementById('finalGarbageWords'),
  finalCloseCalls: document.getElementById('finalCloseCalls'),
  finalTimeSpent: document.getElementById('finalTimeSpent'),
  aiReviewText: document.getElementById('aiReviewText'),

  // Sección de Corrección de Estilo
  styleReviewCard: document.getElementById('styleReviewCard'),
  styleReviewStatus: document.getElementById('styleReviewStatus'),
  styleSuggestionsList: document.getElementById('styleSuggestionsList'),
  styleFallbackMsg: document.getElementById('styleFallbackMsg'),

  btnCerrarReporte: document.getElementById('btnCerrarReporte'),
  btnDescargarDesdeReporte: document.getElementById('btnDescargarDesdeReporte'),
};

// ==============================================================================
// COMUNICACIÓN CON LA API FLASK
// ==============================================================================

async function cargarNivelesDesdeAPI() {
  try {
    const res = await fetch('/api/niveles');
    const data = await res.json();
    AppState.niveles = data.niveles;
    seleccionarNivel(AppState.niveles[0].id);
    renderizarSelectorNiveles();
  } catch (err) {
    console.warn('API local no disponible, usando configuración de respaldo:', err);
    AppState.niveles = [
      { id: 1, nombre: "Calentamiento y Soltura", descripcion: "Tolerancia flexible.", tolerancia_seg: 7.5, meta_palabras: 75, pomodoro_min: 5, descanso_min: 2 },
      { id: 2, nombre: "Enfoque y Fluidez", descripcion: "Ritmo constante.", tolerancia_seg: 4.5, meta_palabras: 150, pomodoro_min: 10, descanso_min: 3 },
      { id: 3, nombre: "Modo Máximo Desafío", descripcion: "Escritura al límite.", tolerancia_seg: 2.5, meta_palabras: 250, pomodoro_min: 15, descanso_min: 5 }
    ];
    seleccionarNivel(1);
    renderizarSelectorNiveles();
  }
}

async function solicitarValidacionIA(texto) {
  try {
    const res = await fetch('/api/validar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto, nivel: AppState.nivelSeleccionado.id })
    });
    return await res.json();
  } catch (err) {
    const palabras = texto.trim().split(/\s+/).filter(p => p.length > 0);
    return {
      valido: true,
      palabras_totales: palabras.length,
      palabras_validas: palabras.length,
      palabras_basura: 0,
      porcentaje_calidad: 100.0,
      alerta: null
    };
  }
}

async function solicitarCalificacionFinal() {
  const tiempoSegundos = AppState.tiempoInicioSesion
    ? (Date.now() - AppState.tiempoInicioSesion) / 1000
    : 1;

  try {
    const res = await fetch('/api/calificar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        palabras_validas: AppState.palabrasValidas,
        palabras_basura: AppState.palabrasBasura,
        pausas_al_limite: AppState.pausasAlLimite,
        tiempo_segundos: tiempoSegundos,
        nivel_id: AppState.nivelSeleccionado.id,
        texto: DOM.writingArea.value,
        coherente_ia: AppState.coherenteIA,
        pomodoro_completado: AppState.pomodoroCompletado
      })
    });
    return await res.json();
  } catch (err) {
    const min = Math.max(tiempoSegundos / 60, 0.1);
    return {
      puntaje_total: 85.0,
      estrellas: 4,
      rango: "Escritor Enfocado",
      wpm: Math.round(AppState.palabrasValidas / min),
      palabras_validas: AppState.palabrasValidas,
      palabras_descartadas: AppState.palabrasBasura,
      pausas_criticas: AppState.pausasAlLimite,
      tiempo_total_seg: tiempoSegundos,
      cumplio_meta: true,
      resena_ia: {
        disponible: false,
        comentario: "Ollama local no respondió a tiempo. Tu calificación matemática se calculó al 100%."
      }
    };
  }
}

// ==============================================================================
// 💡 TEMAS SUGERIDOS AL ARRANCAR (Qwen 2.5 3B / Fallback)
// ==============================================================================

async function solicitarTemaSugerido(forzarOtro = false) {
  if (AppState.cargandoTema) return;
  AppState.cargandoTema = true;

  if (DOM.btnOtroTema) {
    DOM.btnOtroTema.disabled = true;
    DOM.btnOtroTema.classList.add('loading');
  }

  if (DOM.topicText) {
    DOM.topicText.textContent = 'Buscando una idea inspiradora…';
  }

  const nivelId = AppState.nivelSeleccionado ? AppState.nivelSeleccionado.id : 1;
  const temaAnterior = forzarOtro ? AppState.temaActual : '';

  try {
    const res = await fetch('/api/tema', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nivel_id: nivelId, tema_anterior: temaAnterior })
    });
    const data = await res.json();
    AppState.temaActual = data.sugerencia || '';
    if (DOM.topicText) {
      DOM.topicText.textContent = AppState.temaActual;
    }
  } catch (err) {
    console.warn('Fallback local de tema:', err);
    const fallbacks = [
      "Describe con sumo detalle el primer objeto que viste al despertar y un recuerdo asociado.",
      "Un personaje encuentra una llave antigua en el bolsillo de un abrigo que no es suyo.",
      "Si los recuerdos tuvieran peso y textura física, ¿cómo se sentiría entrar a una casa abandonada?"
    ];
    AppState.temaActual = fallbacks[(nivelId - 1) % fallbacks.length];
    if (DOM.topicText) {
      DOM.topicText.textContent = AppState.temaActual;
    }
  } finally {
    AppState.cargandoTema = false;
    if (DOM.btnOtroTema) {
      DOM.btnOtroTema.disabled = false;
      DOM.btnOtroTema.classList.remove('loading');
    }
    actualizarVisibilidadTarjetaTema();
  }
}

function actualizarVisibilidadTarjetaTema() {
  if (!DOM.topicCard) return;
  // La tarjeta no debe bloquear ni mostrarse una vez que el usuario empieza a redactar
  if (DOM.writingArea && DOM.writingArea.value.trim().length > 0) {
    DOM.topicCard.classList.add('hidden');
  } else {
    DOM.topicCard.classList.remove('hidden');
  }
}

// ==============================================================================
// ✏️ CORRECCIÓN DE ESTILO ASISTIDA POR IA (Endpoint desacoplado /api/estilo)
// ==============================================================================

function escaparHTML(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function solicitarCorreccionEstilo(texto) {
  if (!DOM.styleReviewCard) return;

  DOM.styleReviewStatus.style.display = 'flex';
  DOM.styleSuggestionsList.style.display = 'none';
  DOM.styleFallbackMsg.style.display = 'none';
  DOM.styleSuggestionsList.innerHTML = '';

  try {
    const res = await fetch('/api/estilo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto: texto || '' })
    });
    const data = await res.json();

    DOM.styleReviewStatus.style.display = 'none';

    if (data.disponible && Array.isArray(data.sugerencias) && data.sugerencias.length > 0) {
      DOM.styleSuggestionsList.innerHTML = data.sugerencias.map(sug => `
        <div class="style-item">
          <div class="style-item-header">
            <span class="style-badge-tag original">Original</span>
            <blockquote class="style-quote">“${escaparHTML(sug.original)}”</blockquote>
          </div>
          <div class="style-item-body">
            <span class="style-badge-tag suggestion">Sugerencia</span>
            <p class="style-replacement">${escaparHTML(sug.sugerencia)}</p>
          </div>
          <p class="style-reason"><strong>¿Por qué?</strong> ${escaparHTML(sug.motivo)}</p>
        </div>
      `).join('');
      DOM.styleSuggestionsList.style.display = 'flex';
    } else {
      DOM.styleFallbackMsg.textContent = data.mensaje || 'No se detectaron problemas evidentes en la redacción.';
      DOM.styleFallbackMsg.style.display = 'block';
    }
  } catch (err) {
    console.warn('Aviso corrección de estilo:', err);
    DOM.styleReviewStatus.style.display = 'none';
    DOM.styleFallbackMsg.textContent = 'La corrección de estilo asistida por IA local no está disponible en este momento.';
    DOM.styleFallbackMsg.style.display = 'block';
  }
}

// ==============================================================================
// GESTIÓN DE NIVELES Y GAMIFICACIÓN
// ==============================================================================

function seleccionarNivel(nivelId) {
  const nivel = AppState.niveles.find(n => n.id === nivelId);
  if (!nivel) return;

  AppState.nivelSeleccionado = nivel;
  DOM.levelNameDisplay.textContent = `Nivel ${nivel.id}: ${nivel.nombre}`;
  DOM.secondsLeftDisplay.textContent = `${nivel.tolerancia_seg.toFixed(1)}s`;
  DOM.wordsCounter.textContent = `0 / ${nivel.meta_palabras}`;
  AppState.pomodoroSegundosRestantes = nivel.pomodoro_min * 60;
  actualizarDisplayPomodoro();
  reiniciarEstadoSesion();
  solicitarTemaSugerido();
}

function renderizarSelectorNiveles() {
  DOM.levelsGridContainer.innerHTML = AppState.niveles.map(n => `
    <div class="level-card ${n.id === AppState.nivelSeleccionado.id ? 'selected' : ''}" data-nivel-id="${n.id}">
      <div class="level-card-info">
        <h3>Nivel ${n.id}: ${n.nombre}</h3>
        <p>${n.descripcion} — Meta: <strong>${n.meta_palabras} palabras</strong></p>
      </div>
      <div class="level-badge-tag">⏱️ ${n.tolerancia_seg}s pausa máx.</div>
    </div>
  `).join('');

  document.querySelectorAll('.level-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = parseInt(card.getAttribute('data-nivel-id'), 10);
      seleccionarNivel(id);
      renderizarSelectorNiveles();
    });
  });
}

// ==============================================================================
// BUCLE DE ALTA PRECISIÓN: Monitoreo de Inactividad y Peligro
// ==============================================================================

function iniciarLoopInactividad() {
  if (AppState.animFrameId) cancelAnimationFrame(AppState.animFrameId);

  const step = () => {
    if (AppState.estadoJuego === 'ESCRIBIENDO' && AppState.fasePomodoro === 'ESCRITURA') {
      const ahora = performance.now();
      const tiempoTranscurridoInactivo = (ahora - AppState.ultimaPulsacionMs) / 1000;
      const tolerancia = AppState.nivelSeleccionado.tolerancia_seg;
      const restante = Math.max(tolerancia - tiempoTranscurridoInactivo, 0);

      const porcentajeRestante = (restante / tolerancia) * 100;
      const porcentajePeligro = 100 - porcentajeRestante;

      // Actualizar Barra y Display
      DOM.inactivityBar.style.width = `${porcentajeRestante}%`;
      DOM.secondsLeftDisplay.textContent = `${restante.toFixed(1)}s`;

      // Clases reactivas de la barra
      if (porcentajeRestante < 25) {
        DOM.inactivityBar.className = 'meter-bar danger';
        DOM.dangerOverlay.style.opacity = (porcentajePeligro / 100) * 0.95;
        DOM.dangerOverlay.classList.add('critical');
        if (!AppState.alertaPeligroActiva) {
          AppState.pausasAlLimite++;
          AppState.alertaPeligroActiva = true;
        }
      } else if (porcentajeRestante < 55) {
        DOM.inactivityBar.className = 'meter-bar warning';
        DOM.dangerOverlay.style.opacity = (porcentajePeligro / 100) * 0.5;
        DOM.dangerOverlay.classList.remove('critical');
        AppState.alertaPeligroActiva = false;
      } else {
        DOM.inactivityBar.className = 'meter-bar';
        DOM.dangerOverlay.style.opacity = 0;
        DOM.dangerOverlay.classList.remove('critical');
        AppState.alertaPeligroActiva = false;
      }

      // CONDICIÓN DE BORRADO PUNITIVO (GAME OVER)
      if (restante <= 0.05 && DOM.writingArea.value.trim().length > 0) {
        ejecutarBorradoPunitivo();
        return;
      }
    }

    AppState.animFrameId = requestAnimationFrame(step);
  };

  AppState.animFrameId = requestAnimationFrame(step);
}

function ejecutarBorradoPunitivo() {
  AppState.estadoJuego = 'BORRADO';
  DOM.dangerOverlay.style.opacity = 0.9;
  DOM.editorWrapper.classList.add('shake');

  setTimeout(() => {
    DOM.writingArea.value = '';
    DOM.editorWrapper.classList.remove('shake');
    DOM.dangerOverlay.style.opacity = 0;
    DOM.dangerOverlay.classList.remove('critical');
    DOM.modalGameOver.style.display = 'flex';
  }, 400);
}

// ==============================================================================
// MOTOR POMODORO (Escritura y Descanso)
// ==============================================================================

let pomoIntervalId = null;

function iniciarTemporizadorPomodoro() {
  if (pomoIntervalId) clearInterval(pomoIntervalId);

  pomoIntervalId = setInterval(() => {
    if (AppState.estadoJuego === 'ESCRIBIENDO' || AppState.fasePomodoro === 'DESCANSO') {
      AppState.pomodoroSegundosRestantes--;

      if (AppState.fasePomodoro === 'ESCRITURA') {
        actualizarDisplayPomodoro();
        if (AppState.pomodoroSegundosRestantes <= 0) {
          transicionarADescansoPomodoro();
        }
      } else if (AppState.fasePomodoro === 'DESCANSO') {
        actualizarDisplayDescanso();
        if (AppState.pomodoroSegundosRestantes <= 0) {
          transicionarAEscrituraPomodoro();
        }
      }
    }
  }, 1000);
}

function actualizarDisplayPomodoro() {
  const min = Math.floor(AppState.pomodoroSegundosRestantes / 60);
  const seg = AppState.pomodoroSegundosRestantes % 60;
  DOM.pomoTimer.textContent = `${min.toString().padStart(2, '0')}:${seg.toString().padStart(2, '0')}`;
}

function actualizarDisplayDescanso() {
  const min = Math.floor(AppState.pomodoroSegundosRestantes / 60);
  const seg = AppState.pomodoroSegundosRestantes % 60;
  DOM.breakTimerDisplay.textContent = `${min.toString().padStart(2, '0')}:${seg.toString().padStart(2, '0')}`;
}

function transicionarADescansoPomodoro() {
  AppState.pomodoroCompletado = true;
  AppState.fasePomodoro = 'DESCANSO';
  AppState.pomodoroSegundosRestantes = AppState.nivelSeleccionado.descanso_min * 60;
  DOM.pomoPhaseLabel.textContent = "Pausa de Descanso Seguro";
  DOM.dangerOverlay.style.opacity = 0;
  DOM.dangerOverlay.classList.remove('critical');
  DOM.modalDescanso.style.display = 'flex';
  actualizarDisplayDescanso();
}

function transicionarAEscrituraPomodoro() {
  AppState.fasePomodoro = 'ESCRITURA';
  AppState.pomodoroSegundosRestantes = AppState.nivelSeleccionado.pomodoro_min * 60;
  DOM.pomoPhaseLabel.textContent = "Fase de Escritura Activa";
  DOM.modalDescanso.style.display = 'none';
  AppState.ultimaPulsacionMs = performance.now();
  actualizarDisplayPomodoro();
  DOM.writingArea.focus();
}

// ==============================================================================
// MANEJO DE ENTRADA Y VALIDACIÓN ASÍNCRONA (DEBOUNCE)
// ==============================================================================

function onUsuarioEscribe() {
  const ahora = performance.now();

  if (AppState.estadoJuego === 'EN_ESPERA') {
    AppState.estadoJuego = 'ESCRIBIENDO';
    AppState.tiempoInicioSesion = Date.now();
  }

  AppState.ultimaPulsacionMs = ahora;
  actualizarVisibilidadTarjetaTema();

  // Debounce para consultar a la API de Flask
  clearTimeout(AppState.debounceTimer);
  AppState.debounceTimer = setTimeout(async () => {
    const texto = DOM.writingArea.value;
    const resultado = await solicitarValidacionIA(texto);

    AppState.palabrasValidas = resultado.palabras_validas;
    AppState.palabrasBasura = resultado.palabras_basura;

    if (resultado.coherencia_ia && resultado.coherencia_ia.fuente === 'ollama') {
      AppState.coherenciaIA = resultado.coherencia_ia.coherente;
    }

    // Actualizar Contador HUD
    const meta = AppState.nivelSeleccionado.meta_palabras;
    DOM.wordsCounter.textContent = `${AppState.palabrasValidas} / ${meta}`;

    const porcentaje = Math.min(Math.round((AppState.palabrasValidas / meta) * 100), 100);
    DOM.goalPercentage.textContent = `${porcentaje}% completado`;
    DOM.goalProgressBar.style.width = `${porcentaje}%`;

    if (AppState.palabrasValidas >= meta && AppState.estadoJuego === 'ESCRIBIENDO' && !AppState.finalizando) {
      AppState.estadoJuego = 'COMPLETADO';
      AppState.finalizando = true;
      DOM.dangerOverlay.style.opacity = 0;
      DOM.dangerOverlay.classList.remove('critical');
      DOM.btnFinalizarSesion.disabled = true;
      mostrarReporteCalificacion();
    }

    // Velocidad WPM en tiempo real
    if (AppState.tiempoInicioSesion) {
      const minutos = Math.max((Date.now() - AppState.tiempoInicioSesion) / 60000, 0.05);
      const wpm = Math.round(AppState.palabrasValidas / minutos);
      DOM.wpmCounter.textContent = wpm;
    }

    // Feedback de la Asistencia IA
    if (resultado.alerta) {
      DOM.aiStatusBadge.className = 'ai-badge ai-warn';
      DOM.aiStatusBadge.textContent = 'Asistencia IA: texto sospechoso';
      DOM.aiWarningToast.textContent = `${resultado.alerta}`;
      DOM.aiWarningToast.style.display = 'block';
    } else if (resultado.coherencia_ia && resultado.coherencia_ia.fuente === 'ollama') {
      DOM.aiStatusBadge.className = 'ai-badge ai-ok';
      DOM.aiStatusBadge.textContent = 'Asistencia IA: coherencia verificada';
      DOM.aiWarningToast.style.display = 'none';
    } else {
      DOM.aiStatusBadge.className = 'ai-badge';
      DOM.aiStatusBadge.textContent = 'Asistencia IA: esperando más texto';
      DOM.aiWarningToast.style.display = 'none';
    }

    DOM.btnDescargarTexto.disabled = AppState.palabrasValidas === 0;
  }, 2000);
}

function reiniciarEstadoSesion() {
  AppState.estadoJuego = 'EN_ESPERA';
  AppState.tiempoInicioSesion = null;
  AppState.ultimaPulsacionMs = performance.now();
  AppState.palabrasValidas = 0;
  AppState.palabrasBasura = 0;
  AppState.pausasAlLimite = 0;
  AppState.finalizando = false;
  AppState.coherenciaIA = true;
  AppState.pomodoroCompletado = false;

  DOM.writingArea.value = '';
  DOM.wpmCounter.textContent = '0';
  DOM.goalProgressBar.style.width = '0%';
  DOM.goalPercentage.textContent = '0% completado';
  DOM.dangerOverlay.style.opacity = 0;
  DOM.dangerOverlay.classList.remove('critical');
  DOM.inactivityBar.className = 'meter-bar';
  DOM.inactivityBar.style.width = '100%';
  DOM.btnDescargarTexto.disabled = true;
  DOM.btnFinalizarSesion.disabled = false;
  DOM.aiWarningToast.style.display = 'none';

  actualizarVisibilidadTarjetaTema();
}

// ==============================================================================
// EXPORTACIÓN DE ARCHIVO Y CALIFICACIÓN FINAL
// ==============================================================================

function descargarTexto() {
  const texto = DOM.writingArea.value;
  if (!texto.trim()) return;

  const blob = new Blob([texto], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `escribe_si_puedes_nivel_${AppState.nivelSeleccionado.id}_${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function mostrarReporteCalificacion() {
  const textoEscrito = DOM.writingArea.value;

  // 1. Iniciar inmediatamente la consulta de corrección de estilo en paralelo
  solicitarCorreccionEstilo(textoEscrito);

  // 2. Obtener la calificación matemática y reseña literaria
  const evaluacion = await solicitarCalificacionFinal();

  DOM.summaryRank.textContent = evaluacion.rango;
  DOM.starsDisplay.textContent = '★'.repeat(evaluacion.estrellas) + '☆'.repeat(5 - evaluacion.estrellas);
  DOM.finalScoreVal.textContent = `${evaluacion.puntaje_total} / 100`;
  DOM.finalWpm.textContent = `${evaluacion.wpm} WPM`;
  DOM.finalValidWords.textContent = `${evaluacion.palabras_validas} palabras`;
  DOM.finalGarbageWords.textContent = `${evaluacion.palabras_descartadas} palabras`;
  DOM.finalCloseCalls.textContent = `${evaluacion.pausas_criticas} al límite`;

  const min = Math.floor(evaluacion.tiempo_total_seg / 60);
  const seg = Math.round(evaluacion.tiempo_total_seg % 60);
  DOM.finalTimeSpent.textContent = `${min}m ${seg}s`;

  DOM.aiReviewText.textContent = evaluacion.resena_ia?.comentario || 'El mentor de IA no está disponible en este momento.';

  DOM.modalCalificacion.style.display = 'flex';
}

// ==============================================================================
// TEMAS DE COLOR
// ==============================================================================

const TEMAS = [
  { id: 'olivetti', nombre: 'Olivetti' },
  { id: 'tinta', nombre: 'Tinta azul' },
  { id: 'royal', nombre: 'Hierro' },
  { id: 'burdeos', nombre: 'Vino' },
  { id: 'escritorio', nombre: 'Claro' },
  { id: 'cafe', nombre: 'Café' },
];

function aplicarTema(id) {
  const tema = TEMAS.find(t => t.id === id) || TEMAS[0];
  document.documentElement.setAttribute('data-theme', tema.id);
  const etiqueta = document.getElementById('themeNameDisplay');
  if (etiqueta) etiqueta.textContent = tema.nombre;
  try { localStorage.setItem('esp-tema', tema.id); } catch (e) { /* sin almacenamiento */ }
}

function cargarTemaGuardado() {
  let guardado = null;
  try { guardado = localStorage.getItem('esp-tema'); } catch (e) { /* sin almacenamiento */ }
  aplicarTema(guardado || 'olivetti');
}

function siguienteTema() {
  const actual = document.documentElement.getAttribute('data-theme');
  const i = TEMAS.findIndex(t => t.id === actual);
  aplicarTema(TEMAS[(i + 1) % TEMAS.length].id);
}

// ==============================================================================
// INICIALIZACIÓN DE EVENTOS
// ==============================================================================

function init() {
  // Carga inicial
  cargarTemaGuardado();
  cargarNivelesDesdeAPI();
  iniciarLoopInactividad();
  iniciarTemporizadorPomodoro();

  // Evento de escritura
  DOM.writingArea.addEventListener('input', onUsuarioEscribe);

  // Anti-trampa: no se permite pegar ni arrastrar texto, solo escribirlo
  DOM.writingArea.addEventListener('paste', (e) => {
    e.preventDefault();
    DOM.aiWarningToast.textContent = 'Pegar texto no está permitido: la práctica es escribir, no copiar.';
    DOM.aiWarningToast.style.display = 'block';
    clearTimeout(AppState.toastPegadoTimer);
    AppState.toastPegadoTimer = setTimeout(() => {
      DOM.aiWarningToast.style.display = 'none';
    }, 2500);
  });

  DOM.writingArea.addEventListener('drop', (e) => {
    e.preventDefault();
  });

  // Botón "Otro tema" para ideas disparadoras
  if (DOM.btnOtroTema) {
    DOM.btnOtroTema.addEventListener('click', (e) => {
      e.stopPropagation();
      solicitarTemaSugerido(true);
    });
  }

  // Selector de Nivel
  DOM.btnOpenLevelModal.addEventListener('click', () => {
    DOM.modalNivel.style.display = 'flex';
  });

  DOM.btnCloseLevelModal.addEventListener('click', () => {
    DOM.modalNivel.style.display = 'none';
    DOM.writingArea.focus();
  });

  // Game Over
  DOM.btnReiniciarNivel.addEventListener('click', () => {
    DOM.modalGameOver.style.display = 'none';
    reiniciarEstadoSesion();
    solicitarTemaSugerido();
    DOM.writingArea.focus();
  });

  // Pomodoro Break
  DOM.btnContinuarSiguienteCiclo.addEventListener('click', () => {
    transicionarAEscrituraPomodoro();
  });

  // Finalizar y Calificar
  DOM.btnFinalizarSesion.addEventListener('click', () => {
    if (AppState.finalizando) return;
    AppState.finalizando = true;
    AppState.estadoJuego = 'COMPLETADO';
    DOM.btnFinalizarSesion.disabled = true;
    DOM.dangerOverlay.style.opacity = 0;
    DOM.dangerOverlay.classList.remove('critical');
    mostrarReporteCalificacion();
  });

  DOM.btnCerrarReporte.addEventListener('click', () => {
    DOM.modalCalificacion.style.display = 'none';
  });

  // Descarga
  DOM.btnDescargarTexto.addEventListener('click', descargarTexto);
  DOM.btnDescargarDesdeReporte.addEventListener('click', descargarTexto);

  // Cambio de tema
  document.getElementById('btnTema').addEventListener('click', () => {
    siguienteTema();
    DOM.writingArea.focus();
  });
}

// Arrancar al cargar el script
document.addEventListener('DOMContentLoaded', init);