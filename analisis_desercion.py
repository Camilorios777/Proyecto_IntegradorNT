import json
import shutil
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

RAW = Path(__file__).parent / "Data" / "raw" / "datos_estudiantes.csv"
PROCESSED = Path(__file__).parent / "Data" / "processed"
GRAFICOS = PROCESSED / "graficos"
WEB_PUBLIC = Path(__file__).parent / "web" / "public"
DASHBOARD_DATA = WEB_PUBLIC / "dashboard.json"
DASHBOARD_GRAFICOS = WEB_PUBLIC / "graficos"
COLUMNAS_REQUERIDAS = [
    "id_estudiante",
    "programa",
    "facultad",
    "jornada",
    "semestre",
    "promedio_acumulado",
    "creditos_aprobados",
    "materias_reprobadas",
    "asistencia_pct",
    "sesiones_tutoria",
    "cambios_programa",
    "estrato",
    "beca",
    "trabaja",
    "horas_trabajo_semana",
    "distancia_km",
    "edad",
    "genero",
    "ciudad_procedencia",
    "tipo_colegio",
    "fecha_matricula",
    "estado",
    "motivo_retiro",
]

# Valores válidos de cada columna categórica (la forma correcta de escribirlos).
VALIDOS = {
    "programa": [
        "Administración de Empresas",
        "Contaduría Pública",
        "Derecho",
        "Psicología",
        "Ingeniería de Sistemas",
        "Ingeniería Industrial",
        "Enfermería",
        "Diseño Gráfico",
    ],
    "jornada": ["Diurna", "Nocturna", "Fin de semana"],
    "genero": ["Femenino", "Masculino"],
    "ciudad_procedencia": ["Bogotá", "Medellín", "Cali", "Bucaramanga", "Rionegro", "Barranquilla", "Otra ciudad"],
}

DECISIONES = []


def registrar(paso, columna, accion, filas, justificacion):
    """Guarda una decisión para la tabla de decisiones. Ya está escrita: solo úsala."""
    DECISIONES.append({
        "paso": paso,
        "columna": columna,
        "accion": accion,
        "filas_afectadas": int(filas),
        "justificacion": justificacion,
    })


def explorar(df):
    """Paso 1 del Word: primera mirada al dataset.

    Muestra la forma, los tipos y los nulos de cada columna, las estadísticas
    numéricas, y los valores de las columnas programa, jornada, genero y estado.
    Pregunta: ¿alguna columna numérica aparece como texto? ¿Por qué crees que pasa?
    """
    print("\n--- Shape ---")
    print(df.shape)
    print("\n--- Info ---")
    df.info()
    print("\n--- Describe ---")
    print(df.describe(include=[np.number]).T)
    for columna in ["programa", "jornada", "genero", "estado"]:
        print(f"\n--- Value counts: {columna} ---")
        print(df[columna].value_counts(dropna=False).to_string())


def auditar(df):
    """Paso 2 del Word: buscar problemas sin corregirlos todavía.

    Revisa: nulos reales, faltantes disfrazados ('-', 999), valores imposibles
    (edad, promedio, horas), duplicados y formatos de fecha.
    Pregunta: ¿cuál de estos problemas afecta más el análisis? ¿Por qué?
    """
    print("\n--- Nulos reales por columna ---")
    print(df.isna().sum().sort_values(ascending=False).to_string())

    print("\n--- Faltantes disfrazados ---")
    print({
        "asistencia_pct": int(df["asistencia_pct"].astype(str).str.contains("%|-", na=False).sum()),
        "horas_trabajo_semana": int(df["horas_trabajo_semana"].astype(str).str.contains("-", na=False).sum()),
        "distancia_km": int(pd.to_numeric(df["distancia_km"], errors="coerce").eq(999).sum()),
    })

    print("\n--- Valores imposibles ---")
    print({
        "promedio_acumulado_mayor_5": int(pd.to_numeric(df["promedio_acumulado"], errors="coerce").gt(5).sum()),
        "edad_fuera_rango": int((pd.to_numeric(df["edad"], errors="coerce") < 12).sum() + (pd.to_numeric(df["edad"], errors="coerce") > 80).sum()),
        "horas_trabajo_semana_ausentes": int(df["horas_trabajo_semana"].astype(str).str.contains("-", na=False).sum()),
    })

    print("\n--- Duplicados ---")
    print(f"Filas duplicadas: {df.duplicated().sum()}")

    print("\n--- Fechas con formato mixto ---")
    fechas_slash = df["fecha_matricula"].astype(str).str.contains("/", na=False).sum()
    fechas_guion = df["fecha_matricula"].astype(str).str.contains("-", na=False).sum()
    print({"con_barra": int(fechas_slash), "con_guion": int(fechas_guion)})


def convertir_numericos(df):
    """Paso 3: columnas que deberían ser numéricas pero llegan como texto."""
    df = df.copy()

    # asistencia_pct: tiene valores como "85%" y también "-"
    texto = df["asistencia_pct"].astype(str)
    con_porcentaje = texto.str.contains("%", regex=False).sum()
    con_guion = texto.eq("-").sum()
    texto = texto.str.replace("%", "", regex=False)
    df["asistencia_pct"] = pd.to_numeric(texto, errors="coerce")  # el "-" queda como nulo
    registrar(3, "asistencia_pct", "quitar el símbolo % y convertir a número", con_porcentaje,
              "Con el símbolo % la columna era texto y no se podía promediar.")
    registrar(3, "asistencia_pct", "cambiar '-' por nulo", con_guion,
              "El guion significa 'sin dato'; se convierte en nulo real.")

    # horas_trabajo_semana: tiene "-" (son estudiantes que no trabajan)
    texto = df["horas_trabajo_semana"].astype(str)
    con_guion = texto.eq("-").sum()
    df["horas_trabajo_semana"] = pd.to_numeric(texto, errors="coerce")
    registrar(3, "horas_trabajo_semana", "cambiar '-' por nulo y convertir a número", con_guion,
              "El guion hacía que la columna fuera texto. Más adelante se decide qué hacer con esos nulos.")

    # distancia_km: el 999 no es una distancia real
    df["distancia_km"] = pd.to_numeric(df["distancia_km"], errors="coerce")
    es_999 = df["distancia_km"].eq(999)
    df.loc[es_999, "distancia_km"] = np.nan
    registrar(3, "distancia_km", "cambiar 999 por nulo", es_999.sum(),
              "999 km no es una distancia real, es un código de 'sin dato'.")
    return df


def unificar_categorias(df):
    """Paso 4: el mismo valor escrito de varias formas (mayúsculas, tildes, F/M)."""
    df = df.copy()
    columnas = ["programa", "jornada", "genero", "ciudad_procedencia"]
    antes = df[columnas].copy()

    # primero quitamos espacios y pasamos todo a minúsculas
    for col in columnas:
        df[col] = df[col].str.strip().str.lower()

    # después cambiamos cada variante por la forma correcta
    df["programa"] = df["programa"].replace({
        "administración de empresas": "Administración de Empresas",
        "contaduría pública": "Contaduría Pública",
        "derecho": "Derecho",
        "psicología": "Psicología",
        "psicologia": "Psicología",
        "ingeniería de sistemas": "Ingeniería de Sistemas",
        "ingenieria de sistemas": "Ingeniería de Sistemas",
        "ingeniería industrial": "Ingeniería Industrial",
        "enfermería": "Enfermería",
        "diseño gráfico": "Diseño Gráfico",
    })
    df["jornada"] = df["jornada"].replace({
        "diurna": "Diurna", "nocturna": "Nocturna", "fin de semana": "Fin de semana",
    })
    df["genero"] = df["genero"].replace({
        "femenino": "Femenino", "f": "Femenino", "masculino": "Masculino", "m": "Masculino",
    })
    df["ciudad_procedencia"] = df["ciudad_procedencia"].replace({
        "bogotá": "Bogotá", "bogota": "Bogotá", "medellín": "Medellín", "medellin": "Medellín",
        "cali": "Cali", "bucaramanga": "Bucaramanga", "rionegro": "Rionegro",
        "barranquilla": "Barranquilla", "otra ciudad": "Otra ciudad",
    })

    # contamos las filas donde al menos una de las 4 columnas cambió de verdad
    cambiaron = (antes.fillna("") != df[columnas].fillna("")).any(axis=1).sum()
    registrar(4, "programa, jornada, genero, ciudad_procedencia", "unificar variantes de escritura", cambiaron,
              "Sin esto 'Psicologia' y 'Psicología' (o 'F' y 'Femenino') contarían como grupos distintos.")
    return df


def convertir_fechas(df):
    """Paso 5: fechas escritas en dos formatos (AAAA-MM-DD y DD/MM/AAAA)."""
    df = df.copy()
    formato_iso = pd.to_datetime(df["fecha_matricula"], format="%Y-%m-%d", errors="coerce")
    formato_latino = pd.to_datetime(df["fecha_matricula"], format="%d/%m/%Y", errors="coerce")
    df["fecha_matricula"] = formato_iso.fillna(formato_latino)
    en_segundo_formato = (formato_iso.isna() & formato_latino.notna()).sum()
    registrar(5, "fecha_matricula", "convertir las dos formas de escribir la fecha a un solo formato", en_segundo_formato,
              "Con dos formatos no se pueden comparar ni ordenar las fechas. Se usó formato explícito para no confundir día y mes.")
    return df


def eliminar_duplicados(df):
    """Paso 6: filas repetidas. Dos estudiantes distintos tendrían id_estudiante diferente."""
    df = df.copy()
    duplicadas = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    registrar(6, "todas", "eliminar filas duplicadas", duplicadas,
              "Eran filas idénticas con el mismo id_estudiante, o sea el mismo estudiante repetido.")
    return df


def tratar_faltantes(df):
    """Paso 7: qué hacer con los nulos que quedan."""
    df = df.copy()

    # promedio_acumulado: se completa con la mediana de su programa
    nulos = df["promedio_acumulado"].isna().sum()
    mediana_programa = df.groupby("programa")["promedio_acumulado"].transform("median")
    df["promedio_acumulado"] = df["promedio_acumulado"].fillna(mediana_programa)
    registrar(7, "promedio_acumulado", "completar con la mediana del programa", nulos,
              "Eliminar estas filas perdería estudiantes. La mediana casi no se afecta por valores extremos y no inventa una nota fuera de lo normal del programa.")

    # ciudad y colegio: se marca como "Sin dato"
    nulos = df["ciudad_procedencia"].isna().sum()
    df["ciudad_procedencia"] = df["ciudad_procedencia"].fillna("Sin dato")
    registrar(7, "ciudad_procedencia", "rellenar con 'Sin dato'", nulos,
              "No se puede adivinar de dónde viene el estudiante; se conserva la fila y se marca que falta.")

    nulos = df["tipo_colegio"].isna().sum()
    df["tipo_colegio"] = df["tipo_colegio"].fillna("Sin dato")
    registrar(7, "tipo_colegio", "rellenar con 'Sin dato'", nulos,
              "No se puede adivinar el tipo de colegio; se conserva la fila y se marca que falta.")

    # distancia_km y asistencia_pct: se dejan como nulo
    registrar(7, "distancia_km", "dejar como nulo", df["distancia_km"].isna().sum(),
              "No se usa en las cinco preguntas e inventar una distancia sería poner un dato falso.")
    registrar(7, "asistencia_pct", "dejar como nulo", df["asistencia_pct"].isna().sum(),
              "No se puede inventar una asistencia. Estos estudiantes no entran en los cuartiles de la pregunta 5.")

    # motivo_retiro: nulo esperado, solo aplica a los desertores
    registrar(7, "motivo_retiro", "no tocar", df["motivo_retiro"].isna().sum(),
              "Está vacío en quienes no desertaron porque la pregunta no aplica. Es un nulo esperado, no un error.")
    return df


def tratar_imposibles(df):
    """Paso 8: valores que no pueden existir."""
    df = df.copy()

    # promedio mayor a 5: la escala es de 0 a 5
    imposibles = df["promedio_acumulado"] > 5
    df.loc[imposibles, "promedio_acumulado"] = np.nan
    mediana_programa = df.groupby("programa")["promedio_acumulado"].transform("median")
    df["promedio_acumulado"] = df["promedio_acumulado"].fillna(mediana_programa)
    registrar(8, "promedio_acumulado", "cambiar promedios mayores a 5 por la mediana del programa", imposibles.sum(),
              "La escala institucional es de 0 a 5, así que 45, 62 o 78 son errores de registro.")

    # edad fuera de 15 a 60 años
    imposibles = (df["edad"] < 15) | (df["edad"] > 60)
    df.loc[imposibles, "edad"] = df["edad"].median()
    registrar(8, "edad", "cambiar edades fuera de 15 a 60 por la mediana", imposibles.sum(),
              "Edades como 150 o 12 años no son posibles en estudiantes de educación superior.")

    # horas de trabajo: si no trabaja, son 0
    no_trabaja = df["trabaja"].eq("no")
    nulos = df.loc[no_trabaja, "horas_trabajo_semana"].isna().sum()
    df.loc[no_trabaja, "horas_trabajo_semana"] = 0
    registrar(8, "horas_trabajo_semana", "poner 0 horas a quienes no trabajan", nulos,
              "Si el estudiante no trabaja, sus horas de trabajo son cero. No es un dato que falte.")

    # horas de trabajo mayores a 100 por semana
    imposibles = df["horas_trabajo_semana"] > 100
    df.loc[imposibles, "horas_trabajo_semana"] = np.nan
    mediana_trabajan = df.loc[~no_trabaja, "horas_trabajo_semana"].median()
    df["horas_trabajo_semana"] = df["horas_trabajo_semana"].fillna(mediana_trabajan)
    registrar(8, "horas_trabajo_semana", "cambiar horas mayores a 100 por la mediana de quienes trabajan", imposibles.sum(),
              "Una semana tiene 168 horas; valores de 200 son imposibles.")
    return df


def crear_variables(df):
    """Paso 9 del Word: variables nuevas para el análisis.

    Crea:
    - desertor: True si estado es 'desertor', False si no.
    - cuartil_asistencia: divide asistencia_pct en cuatro grupos iguales con pd.qcut.
    Pregunta: ¿por qué conviene usar cuartiles y no valores exactos de asistencia?
    """
    df = df.copy()
    df["desertor"] = df["estado"].eq("desertor")
    df["cuartil_asistencia"] = pd.qcut(
        df["asistencia_pct"], q=4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
    )
    return df


def grafico_faltantes(df, output_dir=GRAFICOS):
    """Gráfico 1: porcentaje y cantidad de datos faltantes por columna."""
    faltantes = df.isna().sum().sort_values()
    faltantes = faltantes[faltantes.gt(0)]
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, max(4, len(faltantes) * 0.34)))
    ax.set_title("Registros faltantes por columna", loc="left", fontweight="bold")
    ax.set_xlabel("Porcentaje de registros")
    ax.set_ylabel("")
    if faltantes.empty:
        ax.text(0.5, 0.5, "No se encontraron datos faltantes", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.barh(faltantes.index, faltantes.values, color="#607be7")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor / len(df):.0%}"))
        ax.bar_label(
            ax.containers[0],
            labels=[
                f"{int(total):,}".replace(",", ".") + f" ({total / len(df):.1%})"
                for total in faltantes.values
            ],
            padding=5,
            fontsize=8,
        )
        ax.set_xlim(0, max(faltantes.max() * 1.24, len(df) * 0.05))
    fig.tight_layout()
    fig.savefig(output_dir / "mapa_faltantes.png", dpi=180, bbox_inches="tight")
    plt.close()


def grafico_distribuciones(antes, despues, output_dir=GRAFICOS):
    """Gráfico 2: boxplots de promedio_acumulado y edad, antes y después de limpiar.

    Pregunta: ¿qué cambió en cada distribución? ¿Por qué?
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    sns.boxplot(y=antes["promedio_acumulado"], ax=axes[0, 0], color="lightsteelblue")
    axes[0, 0].set_title("Promedio acumulado · antes")
    axes[0, 0].set_ylabel("Nota (escala de 0 a 5)")
    sns.boxplot(y=despues["promedio_acumulado"], ax=axes[0, 1], color="steelblue")
    axes[0, 1].set_title("Promedio acumulado · después")
    axes[0, 1].set_ylabel("Nota (escala de 0 a 5)")
    sns.boxplot(y=antes["edad"], ax=axes[1, 0], color="lightcoral")
    axes[1, 0].set_title("Edad · antes")
    axes[1, 0].set_ylabel("Años")
    sns.boxplot(y=despues["edad"], ax=axes[1, 1], color="tomato")
    axes[1, 1].set_title("Edad · después")
    axes[1, 1].set_ylabel("Años")

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "distribuciones_antes_despues.png", dpi=180)
    plt.close()


def grafico_tasa_programa(df, output_dir=GRAFICOS):
    """Gráfico 3: tasa de deserción por programa.

    Pista: df.groupby("programa")["desertor"].mean()
    """
    tasa = df.groupby("programa")["desertor"].mean().sort_values(ascending=False).reset_index()
    tasa = tasa.rename(columns={"desertor": "tasa_desercion"})
    fig, ax = plt.subplots(figsize=(10, max(4.5, len(tasa) * 0.55)))
    sns.barplot(data=tasa, x="tasa_desercion", y="programa", orient="h", color="#e98c73", ax=ax)
    ax.set_title("Tasa de deserción por programa", loc="left", fontweight="bold")
    ax.set_xlabel("Estudiantes desertores (% del total del programa)")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor:.0%}"))
    ax.bar_label(
        ax.containers[0],
        labels=[f"{valor:.1%}" for valor in tasa["tasa_desercion"]],
        padding=5,
        fontsize=9,
    )
    ax.set_xlim(0, max(tasa["tasa_desercion"].max() * 1.22, 0.1))
    fig.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "tasa_desercion_por_programa.png", dpi=180, bbox_inches="tight")
    plt.close()


def grafico_tasa_asistencia(df, output_dir=GRAFICOS):
    """Gráfico 4: tasa de deserción por cuartil de asistencia.

    Pista: df.groupby("cuartil_asistencia", observed=True)["desertor"].mean()
    """
    tasa = (
        df.groupby("cuartil_asistencia", observed=True)["desertor"]
        .mean().reindex(["Q1", "Q2", "Q3", "Q4"]).dropna().reset_index()
    )
    tasa = tasa.rename(columns={"desertor": "tasa_desercion"})
    fig, ax = plt.subplots(figsize=(8.5, 5))
    sns.barplot(
        data=tasa,
        x="cuartil_asistencia",
        y="tasa_desercion",
        order=["Q1", "Q2", "Q3", "Q4"],
        color="#637de5",
        ax=ax,
    )
    ax.set_title("Deserción según nivel de asistencia", loc="left", fontweight="bold")
    ax.set_xlabel("Q1 = menor asistencia · Q4 = mayor asistencia")
    ax.set_ylabel("Estudiantes desertores (% del grupo)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor:.0%}"))
    ax.bar_label(
        ax.containers[0],
        labels=[f"{valor:.1%}" for valor in tasa["tasa_desercion"]],
        padding=5,
        fontsize=10,
    )
    ax.set_ylim(0, max(tasa["tasa_desercion"].max() * 1.22, 0.1))
    fig.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "tasa_desercion_por_asistencia.png", dpi=180, bbox_inches="tight")
    plt.close()


def responder_preguntas(df):
    """Paso 10: las cinco preguntas. Cada respuesta muestra cuántos estudiantes hay por grupo."""
    print("\n--- Pregunta 1: ¿qué programa tiene la mayor tasa de deserción? ---")
    p1 = df.groupby("programa").agg(estudiantes=("desertor", "count"), desertores=("desertor", "sum"), tasa=("desertor", "mean"))
    print(p1.sort_values("tasa", ascending=False).to_string())

    print("\n--- Pregunta 2: ¿hay diferencia entre becados y no becados? ---")
    p2 = df.groupby("beca").agg(estudiantes=("desertor", "count"), desertores=("desertor", "sum"), tasa=("desertor", "mean"))
    print(p2.to_string())

    print("\n--- Pregunta 3: ¿qué jornada tiene el menor promedio acumulado? ---")
    p3 = df.groupby("jornada").agg(estudiantes=("promedio_acumulado", "count"), promedio=("promedio_acumulado", "mean"))
    print(p3.sort_values("promedio").to_string())

    print("\n--- Pregunta 4: materias reprobadas de desertores y activos (sin graduados) ---")
    sin_graduados = df[df["estado"] != "graduado"]
    p4 = sin_graduados.groupby("estado").agg(estudiantes=("materias_reprobadas", "count"), promedio_reprobadas=("materias_reprobadas", "mean"))
    print(p4.to_string())

    print("\n--- Pregunta 5: ¿la deserción sube cuando baja la asistencia? ---")
    p5 = df.groupby("cuartil_asistencia", observed=True).agg(
        estudiantes=("desertor", "count"),
        desertores=("desertor", "sum"),
        tasa=("desertor", "mean"),
        asistencia_promedio=("asistencia_pct", "mean"),
    )
    print(p5.to_string())
    print(f"Estudiantes sin dato de asistencia (no entran en los cuartiles): {df['cuartil_asistencia'].isna().sum()}")


def guardar(df):
    """Paso 11 del Word: guardar el dataset limpio y la tabla de decisiones. Ya está escrito."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "dataset_limpio.csv", index=False)
    pd.DataFrame(DECISIONES).to_csv(PROCESSED / "decisiones.csv", index=False)
    print(f"\nDataset limpio guardado: {df.shape[0]} filas, {df.shape[1]} columnas.")


def exportar_dashboard(df, original, origen="datos_estudiantes.csv"):
    """Exporta al frontend React los resultados calculados con el dataset limpio."""
    tasa_programa = (
        df.groupby("programa")
        .agg(total=("id_estudiante", "count"), desertores=("desertor", "sum"))
        .assign(tasa=lambda tabla: tabla["desertores"] / tabla["total"])
        .sort_values("tasa", ascending=False)
    )
    grupos_beca = (
        df.groupby("beca")
        .agg(total=("id_estudiante", "count"), desertores=("desertor", "sum"))
        .assign(tasa=lambda tabla: tabla["desertores"] / tabla["total"])
    )
    grupos_jornada = (
        df.groupby("jornada")["promedio_acumulado"]
        .agg(total="count", promedio="mean")
        .sort_values("promedio")
    )
    grupos_estado = (
        df[~df["estado"].eq("graduado")]
        .groupby("estado")["materias_reprobadas"]
        .agg(total="count", promedio="mean")
    )
    grupos_asistencia = (
        df.groupby("cuartil_asistencia", observed=True)
        .agg(total=("id_estudiante", "count"), desertores=("desertor", "sum"))
        .assign(tasa=lambda tabla: tabla["desertores"] / tabla["total"])
        .reindex(["Q1", "Q2", "Q3", "Q4"])
    )
    conteo_estados = df["estado"].value_counts()
    cantidad_desertores = int(df["desertor"].sum())

    def registros(tabla, indice_nombre):
        resultado = []
        for indice, fila in tabla.iterrows():
            registro = {indice_nombre: str(indice)}
            for columna, valor in fila.items():
                if pd.notna(valor):
                    registro[columna] = float(valor) if isinstance(valor, (float, np.floating)) else int(valor)
            resultado.append(registro)
        return resultado

    programa_principal = tasa_programa.iloc[0]
    jornada_principal = grupos_jornada.iloc[0]
    indice_beca = {str(valor).strip().lower(): valor for valor in grupos_beca.index}
    becados = grupos_beca.loc[indice_beca["sí"]] if "sí" in indice_beca else None
    no_becados = grupos_beca.loc[indice_beca["no"]] if "no" in indice_beca else None
    activos_desertores = grupos_estado.reindex(["activo", "desertor"])

    dashboard = {
        "resumen": {
            "registros_originales": int(len(original)),
            "registros_limpios": int(len(df)),
            "columnas": int(df.shape[1]),
            "columnas_archivo": int(original.shape[1]),
            "origen": origen,
            "desertores": cantidad_desertores,
            "tasa_desercion": cantidad_desertores / len(df),
            "decisiones": len(DECISIONES),
            "estados": [
                {"estado": str(estado), "total": int(total)}
                for estado, total in conteo_estados.items()
            ],
        },
        "generado_en": str(time.time_ns()),
        "respuestas": {
            "programa": {
                "nombre": str(tasa_programa.index[0]),
                "total": int(programa_principal["total"]),
                "desertores": int(programa_principal["desertores"]),
                "tasa": float(programa_principal["tasa"]),
                "grupos": registros(tasa_programa, "nombre"),
            },
            "beca": {
                "becados": {
                    "total": int(becados["total"]),
                    "desertores": int(becados["desertores"]),
                    "tasa": float(becados["tasa"]),
                } if becados is not None else None,
                "no_becados": {
                    "total": int(no_becados["total"]),
                    "desertores": int(no_becados["desertores"]),
                    "tasa": float(no_becados["tasa"]),
                } if no_becados is not None else None,
                "grupos": registros(grupos_beca, "nombre"),
            },
            "jornada": {
                "menor_promedio": str(grupos_jornada.index[0]),
                "grupos": registros(grupos_jornada, "nombre"),
            },
            "materias_reprobadas": {
                "grupos": registros(activos_desertores, "nombre"),
            },
            "asistencia": {
                "grupos": registros(grupos_asistencia, "nombre"),
            },
        },
        "decisiones": DECISIONES,
        "graficos": [
            {
                "titulo": "Datos faltantes por columna",
                "archivo": "mapa_faltantes.png",
                "interpretacion": (
                    "Cada barra representa una columna. Cuanto más larga es, más registros "
                    "faltantes tiene; la etiqueta muestra la cantidad y el porcentaje."
                ),
            },
            {
                "titulo": "Promedios y edades antes y después de limpiar",
                "archivo": "distribuciones_antes_despues.png",
                "interpretacion": (
                    "Compara los valores centrales y los extremos antes y después de "
                    "corregir los datos. Cada recuadro resume la distribución de un grupo."
                ),
            },
            {
                "titulo": "Deserción por programa",
                "archivo": "tasa_desercion_por_programa.png",
                "interpretacion": (
                    "La barra muestra qué porcentaje de estudiantes de cada programa "
                    "desertó. Un porcentaje mayor indica más deserción observada en ese grupo."
                ),
            },
            {
                "titulo": "Deserción por nivel de asistencia",
                "archivo": "tasa_desercion_por_asistencia.png",
                "interpretacion": (
                    "Q1 agrupa la asistencia más baja y Q4 la más alta. Compara los "
                    "porcentajes de deserción de cada grupo; la relación no prueba causalidad."
                ),
            },
        ],
        "reflexiones": {
            "asociacion": (
                "La asociación entre baja asistencia, más materias reprobadas y deserción "
                "no demuestra causalidad. Los resultados describen patrones en estos datos."
            ),
            "motivo_retiro": (
                "No es una variable predictiva válida para anticipar la deserción: solo se "
                "conoce después del retiro y filtraría información posterior al resultado."
            ),
            "uso_responsable": (
                "Las variables sensibles deben analizarse con un propósito legítimo, "
                "protección de datos y revisión de posibles sesgos; no deben interpretarse "
                "como causas individuales."
            ),
        },
    }

    DASHBOARD_DATA.parent.mkdir(parents=True, exist_ok=True)
    with DASHBOARD_DATA.open("w", encoding="utf-8") as archivo:
        json.dump(dashboard, archivo, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Datos del dashboard React guardados: {DASHBOARD_DATA}")
    return dashboard


def analizar_dataset(original, persistir=False, origen="datos_estudiantes.csv", salida_graficos=None, verboso=True):
    """Limpia un dataset del taller y actualiza el dashboard con sus resultados."""
    columnas = original.columns.astype(str).str.strip()
    if columnas.duplicated().any():
        raise ValueError("El CSV contiene nombres de columnas repetidos.")
    original = original.copy()
    original.columns = columnas
    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(original.columns))
    if faltantes:
        raise ValueError(
            "El CSV no tiene todas las columnas del taller. Faltan: "
            + ", ".join(faltantes)
        )
    if original.empty:
        raise ValueError("El CSV no contiene filas para analizar.")

    estados = original["estado"].astype(str).str.strip().str.lower()
    if not estados.isin(["activo", "desertor", "graduado"]).all():
        raise ValueError(
            "La columna estado solo puede contener activo, desertor o graduado."
        )
    if not estados.eq("activo").any() or not estados.eq("desertor").any():
        raise ValueError(
            "El archivo debe tener estudiantes activos y desertores para comparar los resultados."
        )
    for columna in ("programa", "jornada", "beca", "promedio_acumulado", "materias_reprobadas"):
        if original[columna].isna().all():
            raise ValueError(f"La columna {columna} no tiene valores para analizar.")
    asistencia = pd.to_numeric(
        original["asistencia_pct"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace("-", pd.NA),
        errors="coerce",
    )
    if asistencia.nunique() < 4:
        raise ValueError(
            "Se necesitan al menos cuatro valores distintos de asistencia para calcular los cuartiles."
        )

    DECISIONES.clear()
    df = original.copy()
    if verboso:
        explorar(df)
        auditar(df)

    salida_graficos = salida_graficos or GRAFICOS
    grafico_faltantes(df, salida_graficos)

    df = convertir_numericos(df)
    df = unificar_categorias(df)
    df = convertir_fechas(df)
    df = eliminar_duplicados(df)
    df = tratar_faltantes(df)
    df = tratar_imposibles(df)
    df["estado"] = df["estado"].astype(str).str.strip().str.lower()
    df = crear_variables(df)

    if df.empty:
        raise ValueError("No quedaron filas para analizar después de limpiar los duplicados.")
    if df["cuartil_asistencia"].notna().sum() == 0:
        raise ValueError("No fue posible asignar cuartiles de asistencia a los registros.")

    grafico_distribuciones(original, df, salida_graficos)
    grafico_tasa_programa(df, salida_graficos)
    grafico_tasa_asistencia(df, salida_graficos)

    if salida_graficos != DASHBOARD_GRAFICOS:
        DASHBOARD_GRAFICOS.mkdir(parents=True, exist_ok=True)
        for imagen in salida_graficos.glob("*.png"):
            shutil.copy2(imagen, DASHBOARD_GRAFICOS / imagen.name)

    if persistir:
        responder_preguntas(df)
        print("\nTabla de decisiones:")
        print(pd.DataFrame(DECISIONES))
        guardar(df)

    return exportar_dashboard(df, original, origen)


def main():
    original = pd.read_csv(RAW)
    analizar_dataset(original, persistir=True, origen=RAW.name)


if __name__ == "__main__":
    main()
