# PLAN DE PROYECTO

## Embedded Quality Agents

*Framework de Control de Calidad Automatizado para C Embebido*

Versión 1.0 — Mayo 2026

Facultad de Ingeniería — UNER

## 1. Propuesta de Valor

El software embebido opera en entornos donde un defecto puede comprometer vidas humanas, invalidar certificaciones regulatorias o provocar el fallo de sistemas críticos. Sin embargo, la mayor parte de los equipos de desarrollo embebido carecen de procesos de control de calidad automatizados equivalentes a los que existen en el mundo del software de aplicaciones. Los linters se ejecutan manualmente, las revisiones de código dependen exclusivamente del criterio humano y el cumplimiento de estándares como MISRA-C o IEC 62304 se verifica de forma reactiva, tarde en el ciclo de vida del desarrollo.

Embedded Quality Agents resuelve este problema trasladando el modelo de control de calidad progresivo — probado en el framework Python Software Limpio — al dominio del software embebido en lenguaje C. El framework despliega tres agentes inteligentes que actúan en momentos precisos del ciclo de desarrollo: antes del commit, durante la revisión de código y al cierre de cada sprint.

### 1.1 Problema que resuelve

  - La verificación de cumplimiento MISRA-C se realiza manualmente o con herramientas comerciales costosas (PC-lint, QAC).

  - No existe un framework open source integrado que combine análisis de código, diseño y arquitectura para C embebido.

  - La arquitectura en capas exigida por IEC 62304 raramente se verifica de forma automatizada.

  - Los equipos embebidos pierden tiempo en revisiones de código que podrían detectarse con análisis estático previo.

### 1.2 Solución propuesta

Un framework Python de código abierto que orquesta herramientas de análisis estático gratuitas (cppcheck, flawfinder, lizard, GNU complexity) sobre proyectos C embebidos, presentando los resultados de forma unificada, accionable y progresiva según el momento del ciclo de vida.

### 1.3 Beneficios por audiencia

|                                 |                                                                                                                                     |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Audiencia**                   | **Beneficio principal**                                                                                                             |
| **Estudiantes de Posgrado**     | Aprenden calidad de software embebido con herramientas reales, en el contexto de IEC 62304 y MISRA-C, durante el cursado.           |
| **Laboratorios de la Facultad** | Integran control de calidad automatizado en proyectos de investigación y desarrollo de dispositivos médicos sin costo de licencias. |
| **Comunidad Open Source**       | Disponen de un framework extensible, bien documentado y alineado con estándares de la industria para sus proyectos embebidos.       |

## 2. Alcance

La versión 1.0 del framework contempla los siguientes elementos:

### 2.1 Lenguaje y estándares soportados

  - Lenguaje objetivo: C (estándares C99 y C11)

  - Estándar de codificación: MISRA-C 2012 — reglas obligatorias verificables con herramientas gratuitas

  - Marco regulatorio: IEC 62304 — arquitectura en capas de software médico

### 2.2 Agentes incluidos

  - CodeGuard-C: análisis rápido pre-commit (\< 15 segundos)

  - DesignReviewer-C: análisis de diseño a nivel módulo/función (2–10 minutos)

  - ArchitectAnalyst-C: análisis arquitectónico con histórico de sprints (5–30 minutos)

### 2.3 Herramientas externas orquestadas

  - cppcheck ≥ 2.6 — análisis estático general y addon MISRA-C

  - flawfinder — detección de funciones C con vulnerabilidades de seguridad conocidas

  - lizard — complejidad ciclomática, longitud de funciones, conteo de parámetros

  - GNU complexity — complejidad de McCabe por función

### 2.4 Modos de integración

  - Git pre-commit hook (manual o vía framework pre-commit)

  - Makefile target: make quality

  - GitHub Actions / GitLab CI (archivos de workflow incluidos)

  - Ejecución manual desde terminal

### 2.5 Plataformas de host soportadas

  - Linux (Ubuntu 20.04+, Debian 11+)

  - macOS 12+

  - Windows 10/11 mediante WSL2

### 2.6 Configuración

  - Archivo principal: pyproject.toml sección \[tool.embedded-quality-agents\]

  - Fallback: .embedded-qa.toml en la raíz del proyecto

  - Soporte de configuración de capas IEC 62304 para detección de violaciones arquitectónicas

## 3. Fuera de Alcance

Los siguientes elementos están explícitamente excluidos de la versión 1.0:

|                                       |                                                                                                                                                |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Elemento excluido**                 | **Justificación**                                                                                                                              |
| Soporte de C++                        | El foco es C embebido puro. C++ requiere un conjunto de métricas OOP diferente.                                                                |
| Análisis dinámico (Valgrind, ASan)    | Requiere ejecución en plataforma target o emulador. Fuera del alcance del análisis estático.                                                   |
| Análisis de timing y WCET             | El análisis de tiempo de ejecución en el peor caso requiere herramientas especializadas por arquitectura de hardware.                          |
| Análisis de profundidad de stack      | Depende de linker scripts y toolchain específico del target. No generalizable.                                                                 |
| Cobertura completa MISRA-C 2012       | Las reglas que requieren PC-lint o herramientas comerciales están excluidas. Solo se verifica el subset cubierto por cppcheck con addon MISRA. |
| Plugin para IDEs (Keil, IAR, Eclipse) | La integración IDE es una extensión futura. v1.0 se limita a CLI y CI/CD.                                                                      |
| Soporte Windows nativo (sin WSL)      | Las herramientas externas (cppcheck, flawfinder) tienen comportamiento inconsistente en Windows nativo.                                        |
| Integración con IA (Claude API)       | La integración IA para explicaciones y sugerencias está planificada para v1.1. v1.0 es análisis estático puro.                                 |
| Verificación de cobertura de tests    | Requiere entorno de ejecución y framework de testing (Unity, Ceedling). Extensión futura.                                                      |

## 4. Arquitectura

### 4.1 Visión general del sistema

Embedded Quality Agents es un framework Python que sigue el patrón modular establecido en Software Limpio. Cada agente es un orquestador que selecciona y ejecuta verificables (Verifiable) de forma contextual según el tipo de análisis, el presupuesto de tiempo disponible y la configuración del proyecto.

Los agentes no implementan los analizadores desde cero: orquestan herramientas externas gratuitas (cppcheck, flawfinder, lizard) mediante subprocesos Python, parsean sus salidas en formato XML o texto, y las integran con verificaciones propias implementadas mediante análisis de texto y expresiones regulares sobre el código C fuente.

### 4.2 Pipeline temporal

|                               |                                 |                                 |
| ----------------------------- | ------------------------------- | ------------------------------- |
| **CodeGuard-C**               | **DesignReviewer-C**            | **ArchitectAnalyst-C**          |
| Pre-commit \< 15 segundos     | PR Review 2–10 minutos          | Fin de Sprint 5–30 minutos      |
| Archivos modificados          | Módulos + dependencias directas | Sistema completo                |
| Solo advierte — nunca bloquea | Bloquea si CRITICAL             | Solo informa — histórico SQLite |

### 4.3 Estructura del repositorio

El proyecto se distribuye como paquete Python independiente:

> embedded-quality-agents/ src/ embedded\_quality\_agents/ shared/ ← Verifiable, ExecutionContext, QualityConfig codeguard\_c/ ← Agente pre-commit checks/ ← MisraCheck, SecurityCheck, ComplexityCheck... agent.py orchestrator.py designreviewer\_c/ ← Agente de diseño analyzers/ ← ModuleCouplingAnalyzer, IncludeGraphAnalyzer... architectanalyst\_c/ ← Agente arquitectónico metrics/ ← LayerViolationsMetric, CouplingMetric... snapshot\_store.py tests/ docs/ examples/ pyproject.toml

### 4.4 Patrón Verifiable (heredado de Software Limpio)

Cada verificación individual hereda de la clase base Verifiable, declarando su nombre, categoría, duración estimada y prioridad. El orquestador selecciona qué verificables ejecutar según el presupuesto de tiempo disponible y el contexto de análisis (pre-commit, PR review, sprint-end). Este patrón permite agregar nuevos checks sin modificar el núcleo del agente.

### 4.5 Herramientas externas y su rol

|                    |                    |                                                                                                                                        |
| ------------------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Herramienta**    | **Agente**         | **Rol en el framework**                                                                                                                |
| cppcheck           | CodeGuard / Design | Análisis estático general + addon MISRA-C 2012. Detecta errores, warnings y violaciones de reglas MISRA obligatorias.                  |
| flawfinder         | CodeGuard          | Detección de funciones C con vulnerabilidades conocidas: gets(), strcpy(), sprintf() sin bounds, etc.                                  |
| lizard             | CodeGuard / Design | Complejidad ciclomática por función, longitud de funciones (LOC), cantidad de parámetros.                                              |
| GNU complexity     | Design             | Complejidad de McCabe detallada por función como segundo punto de verificación de complejidad.                                         |
| Python ast / regex | Todos              | Análisis propio del código C: grafo de includes, detección de variables globales, guardas de cabecera, violaciones de capas IEC 62304. |

## 5. Especificación de Agentes y Métricas

### 5.1 CodeGuard-C

#### Propósito

Validación rápida de calidad básica del código C antes de cada commit. Actúa sobre los archivos .c y .h modificados en el commit actual. Nunca bloquea el commit — su rol es informar y educar al desarrollador en el momento en que escribe el código.

#### Activación y contexto

  - Trigger: pre-commit hook (Git) o ejecución manual

  - Alcance: solo archivos .c y .h del commit en curso

  - Presupuesto de tiempo: 15 segundos máximo

  - Comportamiento ante errores: exit code 0 siempre (nunca bloquea)

#### Métricas verificadas

|        |                                             |                        |               |                                                    |
| ------ | ------------------------------------------- | ---------------------- | ------------- | -------------------------------------------------- |
| **\#** | **Métrica**                                 | **Herramienta**        | **Severidad** | **Umbral / Descripción**                           |
| 1      | Violaciones MISRA-C Obligatorias            | cppcheck + addon misra | **CRITICAL**  | 0 violaciones de reglas obligatorias (Mandatory)   |
| 2      | Funciones inseguras (gets, strcpy, sprintf) | flawfinder             | **ERROR**     | Nivel de riesgo ≥ 4 en flawfinder                  |
| 3      | Variables no inicializadas                  | cppcheck               | **ERROR**     | Detección de uso antes de asignación               |
| 4      | Desreferencia de puntero nulo               | cppcheck               | **ERROR**     | Acceso a puntero sin verificación previa           |
| 5      | Buffer overflow potencial                   | cppcheck               | **ERROR**     | Escritura fuera de límites detectada estáticamente |
| 6      | Complejidad ciclomática por función \> 10   | lizard                 | **WARNING**   | Umbral configurable. Default: CC \> 10             |
| 7      | Funciones \> 50 líneas                      | lizard                 | **WARNING**   | Umbral configurable. Default: 50 LOC               |
| 8      | Violaciones MISRA-C Requeridas              | cppcheck + addon misra | **WARNING**   | Reglas Required no cumplidas (no bloquea)          |
| 9      | Macros sin paréntesis de protección         | cppcheck               | **WARNING**   | \#define sin paréntesis en expresiones             |
| 10     | Includes no utilizados                      | cppcheck               | **INFO**      | Cabeceras incluidas pero no referenciadas          |

### 5.2 DesignReviewer-C

#### Propósito

Análisis profundo de calidad de diseño a nivel módulo (translation unit) y función. Se ejecuta antes del merge de un Pull Request o de forma planificada semanalmente. Bloquea el proceso si detecta violaciones de severidad CRITICAL, garantizando que el mal diseño no ingrese a la rama principal del repositorio.

#### Activación y contexto

  - Trigger: manual, GitHub Actions en PR con label 'design-review', o ejecución semanal

  - Alcance: módulos .c/.h modificados más sus dependencias directas (includes)

  - Presupuesto de tiempo: 2–10 minutos

  - Comportamiento ante CRITICAL: exit code 1 (bloquea el merge)

  - Comportamiento ante WARNING: exit code 0 (no bloquea, registra deuda técnica)

#### Métricas verificadas

|        |                                            |                                        |               |                                                                              |
| ------ | ------------------------------------------ | -------------------------------------- | ------------- | ---------------------------------------------------------------------------- |
| **\#** | **Métrica**                                | **Herramienta**                        | **Severidad** | **Umbral / Descripción**                                                     |
| 1      | Dependencias circulares entre headers      | Python (análisis de grafo de includes) | **CRITICAL**  | 0 ciclos en el grafo de dependencias de cabeceras                            |
| 2      | Violaciones de capa IEC 62304              | Python (regex sobre includes)          | **CRITICAL**  | Application incluye directamente Platform/Driver. Configurable por proyecto. |
| 3      | Variables globales mutables sin protección | cppcheck + regex propio                | **CRITICAL**  | Variables globales no const accesibles desde múltiples módulos               |
| 4      | Funciones con CC \> 15                     | lizard / GNU complexity                | **CRITICAL**  | Complejidad ciclomática extrema por función                                  |
| 5      | Fan-out de módulo \> 12                    | Python (conteo de includes)            | **CRITICAL**  | Un .c incluye más de 12 cabeceras distintas                                  |
| 6      | Funciones \> 80 líneas                     | lizard                                 | **WARNING**   | Umbral configurable. Default: 80 LOC                                         |
| 7      | Parámetros por función \> 6                | lizard                                 | **WARNING**   | Umbral configurable. Default: 6 parámetros                                   |
| 8      | Ausencia de include guard (\#ifndef)       | Python (regex)                         | **WARNING**   | Cabeceras .h sin protección contra inclusión múltiple                        |
| 9      | Tipos no portables (int, short, long)      | cppcheck + regex                       | **WARNING**   | Uso de tipos cuyo tamaño depende de la plataforma                            |
| 10     | Casts explícitos de puntero peligrosos     | cppcheck                               | **WARNING**   | Conversiones que pueden causar aliasing o pérdida de tipo                    |
| 11     | Profundidad de anidamiento \> 4            | lizard                                 | **WARNING**   | Estructuras de control anidadas más de 4 niveles                             |
| 12     | MISRA-C Advisory no cumplidas              | cppcheck + addon misra                 | **INFO**      | Reglas aconsejadas no satisfechas (informativo)                              |

### 5.3 ArchitectAnalyst-C

#### Propósito

Análisis estratégico de la salud arquitectónica del sistema completo al cierre de cada sprint. Calcula métricas de acoplamiento e inestabilidad por módulo siguiendo el modelo de Robert C. Martin, verifica el cumplimiento de la arquitectura en capas requerida por IEC 62304 y guarda snapshots históricos en SQLite para calcular tendencias entre sprints.

No bloquea el desarrollo. Su rol es estratégico: proveer al equipo información objetiva sobre la evolución de la arquitectura para tomar decisiones de refactorización antes de que la deuda técnica se vuelva inmanejable.

#### Activación y contexto

  - Trigger: manual, milestone de GitHub, o fin de sprint en CI/CD

  - Alcance: sistema completo (todos los .c y .h del proyecto)

  - Presupuesto de tiempo: 5–30 minutos según tamaño del proyecto

  - Comportamiento: exit code 0 siempre — análisis informativo

  - Persistencia: SQLite en .quality\_control/embedded\_architecture.db

#### Métricas verificadas

|        |                                              |               |               |                                                                |
| ------ | -------------------------------------------- | ------------- | ------------- | -------------------------------------------------------------- |
| **\#** | **Métrica**                                  | **Categoría** | **Severidad** | **Umbral / Descripción**                                       |
| 1      | Layer Violations (IEC 62304)                 | Arquitectura  | **CRITICAL**  | Cualquier importación que viole la jerarquía de capas definida |
| 2      | Ciclos de dependencias entre módulos         | Dependencias  | **CRITICAL**  | 0 ciclos a nivel de módulos completos (no solo headers)        |
| 3      | Ca — Afferent Coupling                       | Martin        | **INFO ↑↓=**  | Módulos que dependen de este módulo (responsabilidad)          |
| 4      | Ce — Efferent Coupling                       | Martin        | **INFO ↑↓=**  | Módulos de los que depende este módulo (fragilidad)            |
| 5      | I — Instability (Ce / Ca+Ce)                 | Martin        | **WARNING**   | I \> 0.8 indica módulo muy inestable                           |
| 6      | A — Abstractness                             | Martin        | **INFO ↑↓=**  | Proporción de interfaces/tipos opacos sobre total              |
| 7      | D — Distance from Main Sequence              | Martin        | **CRITICAL**  | |A+I-1| \> 0.5 = CRITICAL · \> 0.3 = WARNING                   |
| 8      | Módulos en Zone of Pain (D \> 0.5, I \< 0.2) | Martin        | **WARNING**   | Módulos estables pero concretos: imposibles de cambiar         |
| 9      | Cobertura MISRA-C del proyecto (%)           | Calidad       | **INFO ↑↓=**  | Porcentaje de archivos sin violaciones MISRA obligatorias      |
| 10     | Tendencia de CC promedio del proyecto        | Calidad       | **INFO ↑↓=**  | Complejidad ciclomática promedio respecto al sprint anterior   |

## 6. Administración de la Configuración

### 6.1 Archivo de configuración principal

El framework utiliza pyproject.toml como archivo de configuración primario cuando el proyecto C lo incluye (por ejemplo, en proyectos con scripts Python auxiliares). Para proyectos puramente C, se soporta el archivo .embedded-qa.toml en la raíz del repositorio como alternativa equivalente.

### 6.2 Estructura de configuración

> \[tool.codeguard-c\] \# Umbrales de análisis max\_cyclomatic\_complexity = 10 max\_function\_lines = 50 misra\_mandatory = true misra\_required = true misra\_advisory = false \# Herramientas habilitadas enable\_cppcheck = true enable\_flawfinder = true enable\_lizard = true \# Exclusiones exclude = \["third\_party/", "build/", "test/mocks/"\] \[tool.designreviewer-c\] max\_fan\_out = 12 max\_function\_lines = 80 max\_parameters = 6 max\_nesting\_depth = 4 max\_cc\_critical = 15 \[tool.architectanalyst-c\] db\_path = ".quality\_control/embedded\_architecture.db" max\_instability = 0.8 max\_distance\_warning = 0.3 max\_distance\_critical = 0.5 \# Arquitectura en capas IEC 62304 \[tool.architectanalyst-c.layers\] platform = \[\] hal = \["platform"\] bsp = \["hal", "platform"\] drivers = \["hal", "bsp"\] application = \["drivers", "hal"\] services = \["application"\]

### 6.3 Versionado del framework

  - Esquema: Semantic Versioning (SemVer) — MAJOR.MINOR.PATCH

  - v1.0.0: tres agentes funcionales con herramientas gratuitas y soporte MISRA-C / IEC 62304

  - v1.1.0 (planificada): integración IA opt-in para explicaciones y sugerencias

  - v1.2.0 (planificada): soporte de cobertura de tests (Unity / Ceedling)

  - Repositorio: GitHub — embedded-quality-agents

  - Distribución: PyPI — pip install embedded-quality-agents

### 6.4 Gestión de dependencias

El framework declara sus dependencias en pyproject.toml:

  - Python ≥ 3.11

  - click (CLI), rich (output en consola), tomli (parseo de configuración)

  - cppcheck ≥ 2.6 (dependencia de sistema, no Python — verificada en instalación)

  - flawfinder, lizard — instalables vía pip

  - GNU complexity — dependencia de sistema opcional

## 7. Restricciones

### 7.1 Restricciones técnicas

  - El framework requiere Python ≥ 3.11 instalado en el host de desarrollo.

  - cppcheck ≥ 2.6 debe estar instalado como herramienta de sistema (no se instala automáticamente vía pip).

  - El addon MISRA-C de cppcheck requiere Python disponible en el PATH del sistema para ejecutarse.

  - En Windows, la ejecución nativa no está soportada en v1.0 — se requiere WSL2.

  - El análisis es exclusivamente estático: no se ejecuta el código C ni se requiere un toolchain de compilación cruzada.

  - La verificación de violaciones de capas IEC 62304 depende de que el usuario defina correctamente la arquitectura en la sección \[tool.architectanalyst-c.layers\] del archivo de configuración.

### 7.2 Restricciones normativas

  - La cobertura MISRA-C 2012 está limitada al subset verificable con cppcheck (aproximadamente 70–80% de las reglas Mandatory y Required). Las reglas que requieren análisis de flujo de datos interprocedural no están cubiertas en v1.0.

  - El framework no reemplaza una auditoría formal de cumplimiento IEC 62304. Sirve como herramienta de apoyo continuo, no como evidencia de certificación.

  - Las decisiones sobre clasificación de software médico (Clase A, B o C según IEC 62304) son responsabilidad del equipo de desarrollo y no están automatizadas.

### 7.3 Restricciones de herramientas externas

  - flawfinder es Python 2/3 compatible pero su modelo de riesgos no se actualiza desde 2022. Las funciones marcadas como riesgosas son correctas, pero nuevas vulnerabilidades no estarán incluidas.

  - lizard no distingue entre código de producción y código de test: se recomienda configurar exclusiones explícitas para directorios de test.

  - GNU complexity puede no estar disponible en todas las distribuciones Linux. El framework lo trata como herramienta opcional; si no está instalada, las métricas correspondientes se omiten sin error.

### 7.4 Restricciones de alcance y diseño

  - El framework analiza código C, no el comportamiento del sistema. Defectos que solo se manifiestan en ejecución (race conditions, deadlocks, desbordamiento de stack real) están fuera del alcance.

  - La abstracción (A) en las métricas de Martin se aproxima mediante la proporción de tipos opacos (structs incompletas, typedefs de puntero a struct) sobre el total de tipos definidos. Esta es una aproximación, no una medida exacta de abstracción en C.

  - El rendimiento del análisis en proyectos con más de 500 archivos .c puede superar el presupuesto de tiempo de CodeGuard-C. Se recomienda configurar exclusiones para directorios generados (build/, third\_party/).

*Embedded Quality Agents — Plan de Proyecto v1.0 | Facultad de Ingeniería UNER | Mayo 2026*
