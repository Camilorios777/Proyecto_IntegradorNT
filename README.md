# Taller práctico proyecto integrador: calidad de datos para la retención estudiantil

Una institución de educación superior quiere entender qué factores están asociados a la deserción, para diseñar estrategias de retención tempranas. Antes de responder preguntas de análisis, el equipo de datos debe garantizar que la información sea confiable. Este taller trabaja justo ese paso: auditar, limpiar y documentar los datos, y después responder cinco preguntas con esos datos limpios.

Los datos son sintéticos. Fueron generados para el taller y no corresponden a estudiantes reales.

## Requisitos

- Python 3.10 o superior
- Git
- Lo visto en los talleres de Pandas y de limpieza de datos

## Cómo empezar

1. Clona el repositorio y entra a la carpeta del proyecto:

   ```
   git clone <URL-DEL-REPOSITORIO>
   cd <NOMBRE-DE-LA-CARPETA>
   ```

2. Crea y activa un ambiente virtual. Las instrucciones para Windows y Mac/Linux están en `LEEME_ambiente.txt`.

3. Instala las librerías:

   ```
   pip install -r requirements.txt
   ```

4. Ejecuta el script:

   ```
   python analisis_desercion.py
   ```

Ejecuta el comando desde la carpeta del proyecto.

## Estructura del proyecto

```
proyecto/
├── analisis_desercion.py   Script principal. Tiene un TODO por cada paso.
├── requirements.txt        Versiones de las librerías.
├── LEEME_ambiente.txt      Pasos para crear el ambiente virtual.
├── README.md               Este archivo.
├── .gitignore              Archivos que Git no debe subir.
└── Data/
    ├── raw/
    │   └── datos_estudiantes.csv   Dataset original. No lo modifiques.
    └── processed/
        ├── .gitkeep                Mantiene la carpeta en el repositorio.
        ├── dataset_limpio.csv      Lo genera el script. No se sube (está en .gitignore).
        ├── decisiones.csv          Lo genera el script. Sí se sube.
        └── graficos/               Lo genera el script. Sí se sube.
```

Lo que genera el script (`dataset_limpio.csv`, `decisiones.csv` y `graficos/`) aparece en `Data/processed/` al ejecutarlo. Los dos últimos se suben al repositorio, porque son parte de la entrega.

## Qué debes hacer

Completa los TODO de `analisis_desercion.py` en orden. Cada función tiene un docstring con preguntas: respóndelas antes de escribir el código. Cada decisión que tomes debe quedar registrada con `registrar()`.

Cuando termines, el script debe producir:

- `Data/processed/dataset_limpio.csv`: el dataset limpio.
- `Data/processed/decisiones.csv`: la tabla de decisiones.
- `Data/processed/graficos/`: los cuatro gráficos.

La guía del taller (`Taller_Retencion_Estudiantil.pdf`) explica cada método antes de usarlo, con ejemplos y errores frecuentes.

## Entrega

Sube tu código completo al repositorio y envía el enlace por el formulario de entrega. La entrega es individual.

El repositorio debe incluir:

- `analisis_desercion.py` con todos los TODO completados.
- `Data/processed/decisiones.csv` y la carpeta `Data/processed/graficos/`.
- Un `README.md` al final de este archivo, con una sección titulada **Mis decisiones y respuestas**. Debe incluir:
  0. El diccionario de datos: la tabla de las 23 columnas con tipo, descripción y rol, completada según el paso 1 de la guía.
  1. Tu diagnóstico de calidad: qué problemas encontraste y en qué columnas.
  2. Tus decisiones de limpieza, con su justificación.
  3. Las respuestas a las cinco preguntas, cada una con el número de estudiantes por grupo.
  4. Tu respuesta a la reflexión sobre asociación y causalidad.
  5. Tu respuesta a la reflexión sobre `motivo_retiro` y la predicción.
  6. Tu respuesta a la reflexión sobre el uso de variables sensibles.

El script debe ejecutarse sin errores desde cero. Cada decisión necesita una justificación, y cada conclusión debe apoyarse en un número del análisis.

## Mis decisiones y respuestas

### 0. Diccionario de datos

| Columna | Tipo | Descripción | Rol |
|---|---|---|---|
| id_estudiante | texto | Identificador único del estudiante en la base. | Identificación |
| programa | categórica | Programa académico en el que está matriculado. | Explicativa |
| facultad | categórica | Facultad a la que pertenece el programa. | Explicativa |
| jornada | categórica | Modalidad de atención: diurna, nocturna o fin de semana. | Explicativa |
| semestre | numérica | Semestre actual del estudiante. | Explicativa |
| promedio_acumulado | numérica | Promedio académico acumulado por el estudiante. | Explicativa |
| creditos_aprobados | numérica | Número de créditos aprobados. | Explicativa |
| materias_reprobadas | numérica | Número de materias reprobadas. | Explicativa |
| asistencia_pct | numérica | Porcentaje de asistencia a clases. | Explicativa |
| sesiones_tutoria | numérica | Número de sesiones de tutoría asistidas. | Explicativa |
| cambios_programa | numérica | Número de cambios de programa reportados. | Explicativa |
| estrato | numérica | Estrato socioeconómico del estudiante. | Explicativa |
| beca | categórica | Indica si el estudiante recibe beca (sí/no). | Explicativa |
| trabaja | categórica | Indica si el estudiante trabaja (sí/no). | Explicativa |
| horas_trabajo_semana | numérica | Horas semanales dedicadas al trabajo. | Explicativa |
| distancia_km | numérica | Distancia en kilómetros entre la residencia y la universidad. | Explicativa |
| edad | numérica | Edad del estudiante. | Explicativa |
| genero | categórica | Género reportado por el estudiante. | Explicativa |
| ciudad_procedencia | categórica | Ciudad de origen o procedencia. | Explicativa |
| tipo_colegio | categórica | Tipo de colegio del que egresó: Público o Privado. | Explicativa |
| fecha_matricula | fecha | Fecha en la que el estudiante se matriculó. | Explicativa |
| estado | categórica | Estado académico del estudiante: activo, graduado o desertor. | Resultado |
| motivo_retiro | categórica | Motivo del retiro si el estudiante desertó. Solo aplica para desertores. | Resultado |

### 1. Diagnóstico de calidad

El archivo original tiene 10.150 filas y 23 columnas. Encontré estos problemas:

| Tipo de problema | Dónde | Cuántos |
|---|---|---|
| Nulos reales | `promedio_acumulado` | 304 |
| Nulos reales | `distancia_km` | 199 |
| Nulos reales | `tipo_colegio` | 152 |
| Nulos reales | `ciudad_procedencia` | 103 |
| Nulo esperado | `motivo_retiro` (solo aplica a desertores) | 6.877 |
| Faltante disfrazado | `asistencia_pct` con `-` | 202 |
| Faltante disfrazado | `horas_trabajo_semana` con `-` (todos son estudiantes que no trabajan) | 2.822 |
| Faltante disfrazado | `distancia_km` con `999` | 152 |
| Formato inconsistente | `asistencia_pct` con el símbolo `%` | 300 |
| Formato inconsistente | `fecha_matricula` en formato DD/MM/AAAA (el resto está en AAAA-MM-DD) | 3.052 |
| Valor imposible | `promedio_acumulado` mayor a 5 (45, 62 y 78) | 17 |
| Valor imposible | `edad` fuera de 15 a 60 (150 años y 12 años) | 12 |
| Valor imposible | `horas_trabajo_semana` mayor a 100 (200 horas) | 30 |
| Duplicados | filas idénticas (mismo `id_estudiante`) | 150 |
| Errores de escritura | `programa`, `jornada`, `genero`, `ciudad_procedencia` | 1.721 filas (después de quitar duplicados) |

Estos problemas cambian los promedios, las tasas y los grupos que se comparan. Por eso se corrigen antes de responder las preguntas.

### 2. Decisiones de limpieza y justificación

Cada decisión queda guardada con su número de filas en `Data/processed/decisiones.csv`.

1. **Columnas de texto a número.** `asistencia_pct`: se quitó el `%` y el `-` pasó a nulo. `horas_trabajo_semana`: el `-` pasó a nulo. `distancia_km`: el `999` pasó a nulo. Sin esto no se pueden calcular promedios.
2. **Errores de escritura.** Se quitaron espacios, se pasó todo a minúsculas y se cambió cada variante por la forma correcta (por ejemplo `Psicologia` → `Psicología`, `F` → `Femenino`). Sin esto el mismo valor se contaría como dos grupos.
3. **Fechas.** Se convirtieron los dos formatos a fecha, usando formato explícito para no confundir día y mes.
4. **Duplicados.** Se eliminaron 150 filas. Eran el mismo estudiante repetido (mismo `id_estudiante`), no estudiantes distintos.
5. **Nulos.**
   - `promedio_acumulado`: se completó con la mediana del programa. Eliminar las filas perdería estudiantes, y la mediana casi no se afecta por valores extremos.
   - `ciudad_procedencia` y `tipo_colegio`: se rellenaron con `Sin dato`, porque no se puede adivinar ese dato.
   - `distancia_km` (347) y `asistencia_pct` (200): se dejaron como nulo. No se inventa un dato. Los 200 sin asistencia no entran en los cuartiles de la pregunta 5.
   - `motivo_retiro`: no se tocó, porque solo aplica a quienes desertaron.
6. **Valores imposibles.**
   - Promedio mayor a 5: se cambió por la mediana del programa (la escala es de 0 a 5).
   - Edad fuera de 15 a 60: se cambió por la mediana de la edad.
   - Horas de trabajo: a quienes no trabajan se les puso 0. Las horas mayores a 100 (una semana tiene 168 horas) se cambiaron por la mediana de quienes sí trabajan.
7. **Variables nuevas.** `desertor` (verdadero si el estado es `desertor`) y `cuartil_asistencia` (cuatro grupos del mismo tamaño según la asistencia, de Q1 a Q4). Se usan cuartiles porque permiten comparar grupos de tamaño parecido en vez de mirar cada porcentaje por separado.

Después de limpiar quedan 10.000 filas y 25 columnas.

### 3. Respuestas a las cinco preguntas

**1. ¿Qué programa tiene la tasa de deserción más alta?**

| Programa | Estudiantes | Desertores | Tasa |
|---|---|---|---|
| Ingeniería Industrial | 1.322 | 531 | 40,17% |
| Ingeniería de Sistemas | 1.432 | 548 | 38,27% |
| Diseño Gráfico | 870 | 311 | 35,75% |
| Enfermería | 1.167 | 365 | 31,28% |
| Derecho | 1.501 | 460 | 30,65% |
| Administración de Empresas | 1.343 | 395 | 29,41% |
| Contaduría Pública | 1.196 | 321 | 26,84% |
| Psicología | 1.169 | 305 | 26,09% |

La más alta es Ingeniería Industrial (40,17%). Ingeniería de Sistemas está muy cerca (38,27%): la diferencia es de menos de 2 puntos, así que no se puede asegurar que Industrial sea realmente mayor que Sistemas. Frente a Psicología (26,09%) sí hay una diferencia clara. Todos los programas tienen más de 800 estudiantes, así que ninguna tasa depende de un grupo pequeño.

**2. ¿Hay diferencia entre becados y no becados?**

| Beca | Estudiantes | Desertores | Tasa |
|---|---|---|---|
| No | 7.243 | 2.631 | 36,32% |
| Sí | 2.757 | 605 | 21,94% |

Los becados desertan menos (21,94% frente a 36,32%). Esto no prueba que la beca cause que se queden: puede que las becas se den a estudiantes que ya tenían más probabilidad de continuar (por ejemplo por sus notas o su situación). Con estos datos solo vemos que las dos cosas van juntas.

**3. ¿Qué jornada tiene el menor promedio acumulado?**

| Jornada | Estudiantes | Promedio |
|---|---|---|
| Nocturna | 2.754 | 3,47 |
| Fin de semana | 984 | 3,70 |
| Diurna | 6.262 | 3,72 |

La jornada Nocturna tiene el promedio más bajo. Los tres grupos son grandes.

**4. ¿Cuántas materias reprobadas tienen en promedio los desertores frente a los activos?**

| Estado | Estudiantes | Promedio de materias reprobadas |
|---|---|---|
| Activos | 5.878 | 0,62 |
| Desertores | 3.236 | 3,07 |

Los desertores reprobaron en promedio 3,07 materias, frente a 0,62 de los activos. Se excluyeron los graduados porque ya terminaron la carrera: no son ni activos ni desertores, y si se mezclan con los activos cambiarían su promedio y la comparación dejaría de ser justa.

**5. ¿La deserción sube cuando baja la asistencia?**

| Cuartil | Estudiantes | Desertores | Tasa | Asistencia promedio |
|---|---|---|---|---|
| Q1 (menor asistencia) | 2.456 | 1.518 | 61,81% | 73,9% |
| Q2 | 2.466 | 912 | 36,98% | 84,4% |
| Q3 | 2.431 | 503 | 20,69% | 91,3% |
| Q4 (mayor asistencia) | 2.447 | 227 | 9,28% | 98,7% |

Sí: cada vez que sube la asistencia, baja la deserción. En Q1 desertan 6 de cada 10 estudiantes y en Q4 menos de 1 de cada 10. Esto no prueba que la baja asistencia cause la deserción: un estudiante que ya piensa en irse puede empezar a faltar. Son 9.800 estudiantes, porque 200 no tienen dato de asistencia.

### 4. Preguntas de los gráficos

- **Gráfico de faltantes.** Los huecos más grandes son `motivo_retiro` (6.877, es esperado), `promedio_acumulado` (304), `distancia_km` (199), `tipo_colegio` (152) y `ciudad_procedencia` (103). Coinciden con los nulos contados en la auditoría. Este gráfico solo muestra nulos reales, no los `-` ni los `999`.
- **Boxplots antes y después.** Antes se veían promedios de 45, 62 y 78 y edades de 150 años; después de limpiar, los promedios quedan entre 1,17 y 5 y las edades entre 17 y 29. Siguen apareciendo algunos puntos sueltos (promedios bajos y edades de 27 a 29), pero son valores posibles, por eso se dejaron.
- **Tasa por programa.** Psicología tiene la tasa más baja e Ingeniería Industrial la más alta. El programa más pequeño es Diseño Gráfico, con 870 estudiantes, que sigue siendo un grupo grande.

### 5. Asociación y causalidad (reflexión 1)

Que los becados deserten menos no quiere decir que la beca sea la causa. Una beca puede darse a estudiantes con buenas notas o con más apoyo en la casa, y esos mismos motivos pueden ayudarles a permanecer. Para saber si la beca causa la permanencia habría que comparar estudiantes parecidos con y sin beca, o repartir las becas al azar y ver qué pasa. Con estos datos solo podemos decir que hay una relación.

### 6. `motivo_retiro` y la predicción (reflexión 2)

`motivo_retiro` solo se conoce después de que el estudiante deserta, así que no sirve para predecir: en un estudiante que todavía está activo la columna está vacía. Usarla sería hacer trampa, porque ya contiene la respuesta. La columna `estado` tiene el mismo problema, porque es justo lo que queremos predecir. También hay que tener cuidado con `promedio_acumulado`, `asistencia_pct`, `creditos_aprobados`, `materias_reprobadas` y `sesiones_tutoria`: si se midieron en el momento del retiro, el estudiante que se fue ya no sumó más créditos ni asistencia, y esos datos ya reflejan la deserción. Para predecir de verdad hay que usar datos tomados antes, por ejemplo al inicio del semestre.

### 7. Variables sensibles (reflexión 3)

No debería usarse el género, el estrato o la ciudad de procedencia para decidir quién recibe apoyo, aunque aparezcan asociados a la deserción. Los riesgos son tratar injustamente a un grupo, estigmatizar a los estudiantes y repetir desigualdades que ya existen. Sí es útil usarlas para revisar si algún grupo está recibiendo menos apoyo. Para decidir el apoyo es mejor usar la situación de cada estudiante (asistencia, materias reprobadas, necesidad).

### 8. Resultado final

Al ejecutar `python analisis_desercion.py` se generan:

- `Data/processed/dataset_limpio.csv`
- `Data/processed/decisiones.csv`
- `Data/processed/graficos/mapa_faltantes.png`
- `Data/processed/graficos/distribuciones_antes_despues.png`
- `Data/processed/graficos/tasa_desercion_por_programa.png`
- `Data/processed/graficos/tasa_desercion_por_asistencia.png`

## Dashboard interactivo en React (extra)

Además del taller, el proyecto incluye un dashboard web que muestra los resultados, los gráficos y las decisiones de limpieza. Lee los datos del archivo `web/public/dashboard.json`, que genera el script de Python.

Necesita Node.js 18 o superior y las librerías de `requirements.txt` instaladas.

Desde la carpeta del proyecto:

```
python -m venv .venv-dashboard
.venv-dashboard\Scripts\python.exe -m pip install -r requirements.txt
.venv-dashboard\Scripts\python.exe analisis_desercion.py
cd web
npm install
npm run dev
```

Cuando aparezca `http://127.0.0.1:5173/`, ábrelo en el navegador. Deja la terminal abierta mientras lo usas: si la cierras, el navegador muestra `ERR_CONNECTION_REFUSED`.

Las siguientes veces solo hace falta entrar a la carpeta `web` y ejecutar `npm run dev`.

La opción **Cargar CSV** analiza otro archivo con las mismas 23 columnas, pero reemplaza los resultados que muestra el dashboard. Para volver a los datos del taller, ejecuta otra vez `analisis_desercion.py`.
