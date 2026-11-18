import { useEffect, useRef, useState } from "react";

const menu = [
  { id: "resumen", label: "Resumen", icon: "◫" },
  { id: "graficos", label: "Gráficos", icon: "▥" },
  { id: "respuestas", label: "Respuestas", icon: "↗" },
  { id: "limpieza", label: "Limpieza", icon: "⌘" },
  { id: "cargar", label: "Cargar CSV", icon: "↑" },
];

const number = (value) =>
  new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 }).format(value);

const decimal = (value) =>
  new Intl.NumberFormat("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

const percent = (value) =>
  new Intl.NumberFormat("es-CO", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);

function Metric({ label, value, detail, accent }) {
  return (
    <article className={`metric-card ${accent}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function BarList({ title, description, data, valueKey, formatValue, color }) {
  const maximum = Math.max(...data.map((item) => item[valueKey]), 0.0001);

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">COMPARACIÓN</p>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      <div className="bar-list">
        {data.map((item) => (
          <div className="bar-row" key={item.nombre}>
            <div className="bar-label">
              <span>{item.nombre}</span>
              <strong>{formatValue(item[valueKey])}</strong>
            </div>
            <div
              className="bar-track"
              role="img"
              aria-label={`${item.nombre}: ${formatValue(item[valueKey])}`}
            >
              <span
                className={`bar-fill ${color}`}
                style={{ width: `${(item[valueKey] / maximum) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [section, setSection] = useState("resumen");
  const [dashboard, setDashboard] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState("");
  const fileInput = useRef(null);

  useEffect(() => {
    fetch("/dashboard.json")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("No se encontraron resultados. Ejecuta primero el análisis de Python.");
        }
        return response.json();
      })
      .then(setDashboard)
      .catch((cause) => setLoadError(cause.message));
  }, []);

  async function analyzeFile(file) {
    if (!file) return;
    setSection("cargar");
    setUploadError("");
    setUploadedFile(file.name);
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setUploadError("Selecciona un archivo con extensión .csv.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "No fue posible analizar este archivo.");
      }
      setDashboard(result);
      setSection("resumen");
    } catch (cause) {
      setUploadError(
        cause instanceof TypeError
          ? "No se pudo conectar con el analizador. Inicia el dashboard con npm run dev y deja abierta su terminal."
          : cause.message,
      );
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  if (loadError) {
    return (
      <main className="load-state">
        <div className="load-card">
          <span className="brand-mark">OP</span>
          <p className="eyebrow">OBSERVATORIO DE PERMANENCIA</p>
          <h1>No se pudieron cargar los resultados</h1>
          <p>{loadError}</p>
          <code>python analisis_desercion.py</code>
        </div>
      </main>
    );
  }

  if (!dashboard) {
    return <main className="load-state">Cargando resultados del análisis…</main>;
  }

  const { resumen, respuestas, decisiones, reflexiones, graficos = [] } = dashboard;
  const activeSection = menu.find((item) => item.id === section);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#inicio" onClick={() => setSection("resumen")}>
          <span className="brand-mark">OP</span>
          <span>
            <strong>Observatorio</strong>
            <small>de permanencia</small>
          </span>
        </a>

        <div className="side-label">ANÁLISIS</div>
        <nav className="navigation" aria-label="Navegación principal">
          {menu.map((item) => (
            <button
              className={section === item.id ? "nav-item active" : "nav-item"}
              key={item.id}
              onClick={() => {
                setSection(item.id);
                setUploadError("");
              }}
              type="button"
            >
              <span className="nav-icon" aria-hidden="true">{item.icon}</span>
              {item.label}
              {section === item.id && <span className="nav-indicator" />}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span>Proyecto integrador <span className="breadcrumb-separator">/</span> Retención estudiantil</span>
          <span className="live-status"><span className="status-dot" /> Fuente: {resumen.origen || "dataset del taller"}</span>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">PANEL DE ANÁLISIS</p>
              <h1>{activeSection.label}</h1>
              <p className="page-description">
                Resultados claros para entender los datos y tomar mejores decisiones.
              </p>
            </div>
            <div className="dataset-badge">
              <span className="badge-icon">▤</span>
              <span>
                <strong>Base analizada</strong>
                <small>{number(resumen.registros_limpios)} registros limpios</small>
              </span>
            </div>
          </div>

          {section === "resumen" && (
            <>
              <div className="metrics-grid">
                <Metric
                  accent="violet"
                  label="Estudiantes analizados"
                  value={number(resumen.registros_limpios)}
                  detail={`${number(resumen.columnas_archivo ?? resumen.columnas)} columnas en el archivo`}
                />
                <Metric
                  accent="coral"
                  label="Tasa de deserción"
                  value={percent(resumen.tasa_desercion)}
                  detail={`${number(resumen.desertores)} estudiantes desertores`}
                />
                <Metric
                  accent="mint"
                  label="Filas repetidas retiradas"
                  value={number(resumen.registros_originales - resumen.registros_limpios)}
                  detail="Duplicados exactos detectados"
                />
                <Metric
                  accent="amber"
                  label="Acciones de limpieza"
                  value={number(resumen.decisiones)}
                  detail="Decisiones registradas y explicadas"
                />
              </div>

              <div className="section-title">
                <div>
                  <p className="eyebrow">VISTA RÁPIDA</p>
                  <h2>Principales resultados</h2>
                </div>
                <button className="text-button" onClick={() => setSection("graficos")} type="button">
                  Explorar gráficos <span aria-hidden="true">→</span>
                </button>
              </div>

              <div className="charts-grid">
                <BarList
                  color="coral"
                  data={respuestas.programa.grupos}
                  description="Porcentaje de estudiantes que desertó en cada programa."
                  formatValue={percent}
                  title="Deserción por programa"
                  valueKey="tasa"
                />
                <BarList
                  color="blue"
                  data={respuestas.asistencia.grupos}
                  description="Q1 tiene menor asistencia; Q4, mayor asistencia."
                  formatValue={percent}
                  title="Deserción según asistencia"
                  valueKey="tasa"
                />
              </div>

              <section className="insight-banner">
                <div className="insight-symbol">✳</div>
                <div>
                  <p className="eyebrow">HALLAZGO PRINCIPAL</p>
                  <h2>La asistencia baja coincide con mayor deserción</h2>
                  <p>
                    En los datos observados, Q1 registra {percent(respuestas.asistencia.grupos[0]?.tasa ?? 0)}
                    {" "}y Q4, {percent(respuestas.asistencia.grupos.at(-1)?.tasa ?? 0)} de deserción.
                    Es una asociación, no una prueba de causalidad.
                  </p>
                </div>
                <button aria-label="Ver respuestas" onClick={() => setSection("respuestas")} type="button">→</button>
              </section>

              <button className="upload-prompt" onClick={() => setSection("cargar")} type="button">
                <span className="upload-prompt-icon">↑</span>
                <span><strong>¿Tienes otro archivo CSV?</strong><small>Cárgalo para actualizar el análisis y los gráficos.</small></span>
                <span className="upload-prompt-link">Analizar otro archivo →</span>
              </button>
            </>
          )}

          {section === "graficos" && (
            <>
              <div className="section-title charts-title">
                <div>
                  <p className="eyebrow">GUÍA VISUAL</p>
                  <h2>Gráficos del análisis</h2>
                  <p>Explora cada gráfico con una explicación sencilla de cómo interpretarlo.</p>
                </div>
              </div>
              <div className="figure-grid">
                {graficos.map((grafico) => (
                  <figure className="panel figure-card" key={grafico.archivo}>
                    <figcaption>
                      <span className="figure-icon">▥</span>
                      <h2>{grafico.titulo}</h2>
                    </figcaption>
                    <img
                      src={`/graficos/${grafico.archivo}?v=${encodeURIComponent(dashboard.generado_en || resumen.origen || "analisis")}`}
                      alt={`Gráfico: ${grafico.titulo}`}
                    />
                    <p className="figure-guide">{grafico.interpretacion}</p>
                  </figure>
                ))}
              </div>
            </>
          )}

          {section === "respuestas" && (
            <div className="answers-list">
              <article className="answer-card featured-answer">
                <span className="question-number">01</span>
                <div className="answer-content">
                  <p className="eyebrow">PROGRAMA CON MAYOR DESERCIÓN</p>
                  <h2>{respuestas.programa.nombre}</h2>
                  <p>Presenta la tasa más alta entre los programas analizados.</p>
                  <div className="answer-stats">
                    <span><strong>{percent(respuestas.programa.tasa)}</strong><small>Tasa de deserción</small></span>
                    <span><strong>{number(respuestas.programa.desertores)}</strong><small>Desertores</small></span>
                    <span><strong>{number(respuestas.programa.total)}</strong><small>Estudiantes</small></span>
                  </div>
                </div>
                <div className="answer-art" aria-hidden="true">↗</div>
              </article>

              <div className="answers-grid">
                <article className="panel answer-panel">
                  <span className="question-number">02</span>
                  <p className="eyebrow">DESERCIÓN POR BECA</p>
                  <h2>¿Hay diferencia entre grupos?</h2>
                  {respuestas.beca.grupos.map((grupo) => (
                    <div className="comparison-row" key={grupo.nombre}>
                      <span>{grupo.nombre.toLowerCase() === "sí" ? "Con beca" : "Sin beca"}</span>
                      <strong>{percent(grupo.tasa)}</strong>
                      <small>{number(grupo.total)} estudiantes</small>
                    </div>
                  ))}
                  <p className="answer-note">La tasa observada es mayor entre quienes no reciben beca.</p>
                </article>

                <article className="panel answer-panel">
                  <span className="question-number">03</span>
                  <p className="eyebrow">PROMEDIO POR JORNADA</p>
                  <h2>¿Qué jornada tiene menor promedio?</h2>
                  {respuestas.jornada.grupos.map((grupo) => (
                    <div className="comparison-row" key={grupo.nombre}>
                      <span>{grupo.nombre}</span>
                      <strong>{decimal(grupo.promedio)}</strong>
                      <small>{number(grupo.total)} estudiantes</small>
                    </div>
                  ))}
                  <p className="answer-note">La jornada con menor promedio es {respuestas.jornada.menor_promedio}.</p>
                </article>

                <article className="panel answer-panel">
                  <span className="question-number">04</span>
                  <p className="eyebrow">MATERIAS REPROBADAS</p>
                  <h2>Desertores frente a estudiantes activos</h2>
                  {respuestas.materias_reprobadas.grupos.map((grupo) => (
                    <div className="comparison-row" key={grupo.nombre}>
                      <span>{grupo.nombre === "activo" ? "Activos" : "Desertores"}</span>
                      <strong>{decimal(grupo.promedio)}</strong>
                      <small>{number(grupo.total)} estudiantes</small>
                    </div>
                  ))}
                  <p className="answer-note">Promedio de materias reprobadas; se excluyeron los graduados.</p>
                </article>

                <article className="panel answer-panel">
                  <span className="question-number">05</span>
                  <p className="eyebrow">DESERCIÓN Y ASISTENCIA</p>
                  <h2>¿Aumenta al bajar la asistencia?</h2>
                  {respuestas.asistencia.grupos.map((grupo) => (
                    <div className="quartile-row" key={grupo.nombre}>
                      <span className={`quartile-tag ${grupo.nombre.toLowerCase()}`}>{grupo.nombre}</span>
                      <div><strong>{percent(grupo.tasa)}</strong><small>{number(grupo.desertores)} de {number(grupo.total)} estudiantes</small></div>
                    </div>
                  ))}
                  <p className="answer-note">La tasa observada aumenta al pasar de Q4 (mayor asistencia) a Q1 (menor asistencia).</p>
                </article>
              </div>

              <div className="section-title reflection-title">
                <div>
                  <p className="eyebrow">REFLEXIONES DEL TALLER</p>
                  <h2>Cómo interpretar y usar los resultados</h2>
                </div>
              </div>
              <section className="reflection-grid">
                <article className="panel reflection-card">
                  <span className="reflection-icon">◎</span>
                  <p className="eyebrow">INTERPRETACIÓN</p>
                  <h2>Asociación no significa causalidad</h2>
                  <p>{reflexiones.asociacion}</p>
                </article>
                <article className="panel reflection-card">
                  <span className="reflection-icon">◷</span>
                  <p className="eyebrow">PREDICCIÓN</p>
                  <h2>Motivo de retiro</h2>
                  <p>{reflexiones.motivo_retiro}</p>
                </article>
                <article className="panel reflection-card">
                  <span className="reflection-icon">◇</span>
                  <p className="eyebrow">USO RESPONSABLE</p>
                  <h2>Variables sensibles</h2>
                  <p>{reflexiones.uso_responsable}</p>
                </article>
              </section>
            </div>
          )}

          {section === "limpieza" && (
            <>
              <section className="cleanup-intro">
                <div className="cleanup-icon">⌘</div>
                <div>
                  <p className="eyebrow">TRAZABILIDAD</p>
                  <h2>Decisiones de limpieza documentadas</h2>
                  <p>Cada acción registra las filas afectadas y explica por qué se aplicó.</p>
                </div>
                <strong>{number(decisiones.length)}<small> decisiones</small></strong>
              </section>
              <section className="panel table-panel">
                <div className="table-scroll">
                  <table>
                    <thead><tr><th>Paso</th><th>Columna</th><th>Acción</th><th>Filas</th><th>Justificación</th></tr></thead>
                    <tbody>
                      {decisiones.map((decision, index) => (
                        <tr key={`${decision.paso}-${decision.columna}-${index}`}>
                          <td><span className="step-pill">{String(decision.paso).padStart(2, "0")}</span></td>
                          <td className="column-name">{decision.columna}</td>
                          <td>{decision.accion}</td>
                          <td>{number(decision.filas_afectadas)}</td>
                          <td className="justification">{decision.justificacion}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {section === "cargar" && (
            <section className="upload-section">
              <div className="upload-copy">
                <span className="upload-large-icon">↑</span>
                <p className="eyebrow">NUEVO ANÁLISIS</p>
                <h2>Carga otro archivo CSV</h2>
                <p>Procesaremos el archivo y actualizaremos los indicadores, las respuestas y los gráficos.</p>
              </div>

              <div className="panel upload-card">
                <div className="upload-dropzone">
                  <span className="dropzone-icon">▤</span>
                  <h3>{uploadedFile || "Selecciona un archivo CSV"}</h3>
                  <p>El archivo debe tener el formato y las columnas del dataset del taller. Máximo 25 MB.</p>
                  <input
                    accept=".csv,text/csv"
                    className="visually-hidden"
                    onChange={(event) => analyzeFile(event.target.files?.[0])}
                    ref={fileInput}
                    type="file"
                  />
                  <button
                    className="primary-button"
                    disabled={uploading}
                    onClick={() => fileInput.current?.click()}
                    type="button"
                  >
                    {uploading ? "Analizando archivo…" : "Elegir archivo"}
                  </button>
                </div>

                {uploadError && <p className="upload-error" role="alert">{uploadError}</p>}
                {uploading && <p className="upload-progress" role="status">Revisando columnas, limpiando los datos y generando gráficos. Esto puede tardar un momento.</p>}

                <div className="requirements">
                  <p className="eyebrow">EL ARCHIVO DEBE CONTENER</p>
                  <p>Las 23 columnas del taller, incluyendo <code>id_estudiante</code>, <code>asistencia_pct</code>, <code>programa</code> y <code>estado</code>.</p>
                  <p>Estados válidos: <strong>activo</strong>, <strong>desertor</strong> y <strong>graduado</strong>. El CSV se analiza localmente y no se conserva el archivo original.</p>
                </div>
              </div>
            </section>
          )}

          <footer className="page-footer">
            <span>Observatorio de permanencia <span className="breadcrumb-separator">·</span> Proyecto Integrador NT</span>
            <span>Resultados calculados desde el archivo analizado</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;
