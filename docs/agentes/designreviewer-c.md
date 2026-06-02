# DesignReviewer-C — Documentación del agente

## Qué hace

DesignReviewer-C analiza la estructura de dependencias de un proyecto C embebido buscando dos categorías de problemas: dependencias circulares entre headers y violaciones de la jerarquía de capas definida según IEC 62304. Está diseñado para correr durante la revisión de un pull request, antes de que el código sea integrado a la rama principal.

El agente no compila el código. Parsea directivas `#include` directamente del texto fuente usando expresiones regulares y construye un grafo de dependencias en memoria. No requiere toolchain, headers del SDK, ni script de build.

A diferencia de CodeGuard-C, DesignReviewer-C retorna **exit code 1 si encuentra findings CRITICAL**, lo que permite usarlo como gate de bloqueo en CI.

---

## Arquitectura interna

```
designreviewer-c <path>
      │
      ▼
  agent.py  (CLI Click)
      │  recolecta *.c y *.h, busca pyproject.toml hacia arriba
      │  carga DesignReviewerConfig (incluye jerarquía de capas)
      ▼
  DesignReviewerOrchestrator
      │  ejecuta los dos analyzers en secuencia
      ├──▶ IncludeGraphAnalyzer   → parsea #include, DFS para ciclos, fan-out
      └──▶ LayerViolationsAnalyzer → determina capa por path, verifica dependencias
                │
                ▼
            list[Finding]
                │
                ▼
  Render: tabla Rich (texto) o JSON
  Exit code: 1 si CRITICAL, 0 si no
```

Cada analyzer recibe un `ExecutionContext` con la lista de archivos filtrada por `exclude_patterns` y retorna una lista de `Finding`. El orquestador agrega todos los findings en un `Report` y mide el tiempo total.

El agent busca `pyproject.toml` comenzando desde el directorio dado y caminando hacia los directorios padre, lo que permite invocar el agente con un subdirectorio (`src/`) sin perder la configuración de capas definida en la raíz del proyecto.

---

## Los dos analyzers

### IncludeGraphAnalyzer

Parsea las directivas `#include "..."` de cada archivo (solo includes locales con comillas; los includes de sistema con `<>` son ignorados). Construye un grafo dirigido donde los nodos son archivos y las aristas representan relaciones de dependencia.

**Detección de ciclos (INC001):** aplica un DFS con coloreo blanco/gris/negro. Cuando el algoritmo encuentra un nodo ya marcado como "en proceso" (gris), extrae el ciclo desde ese punto en el stack de llamadas. Los ciclos se deduplicán usando `frozenset` para evitar reportar el mismo ciclo desde distintos nodos de entrada.

**Fan-out excesivo (INC002):** cuenta los includes locales distintos de cada archivo. Un módulo con muchos includes directos tiene alto acoplamiento eferente — cualquier cambio en sus dependencias puede requerir recompilación y retesting del módulo.

### LayerViolationsAnalyzer

Determina la capa de cada archivo buscando en sus componentes de path (directorios) una coincidencia con los nombres de capa definidos en la configuración. Un archivo en `src/hal/uart.c` pertenece a la capa `hal`; un archivo en `src/app/logic.c` pertenece a la capa `app`.

Para cada include local en un archivo, resuelve la ruta del archivo incluido y determina su capa. Si la capa del archivo incluido no está en la lista de dependencias permitidas de la capa del archivo fuente, genera un finding CRITICAL.

Los archivos que no pertenecen a ninguna capa definida (ej. `main.c` en la raíz) son ignorados por este analyzer.

---

## Reglas y su valor en código embebido

### INC001 — Dependencia circular entre headers

**Qué detecta:** ciclos en el grafo de includes locales. Ejemplos: `a.h` incluye `b.h` y `b.h` incluye `a.h` (ciclo de dos nodos); o `a.h → b.h → c.h → a.h` (ciclo de tres nodos).

**Por qué importa:** los ciclos de includes producen errores de compilación en el mejor caso y comportamiento indefinido del preprocesador en el peor. En código embebido donde los headers definen estructuras de datos compartidas entre módulos, un ciclo suele indicar que dos módulos tienen dependencias mutuas — una señal de que las responsabilidades no están bien separadas y que el diseño tiene acoplamiento circular.

**Umbral:** 0 ciclos permitidos.

**Severidad:** CRITICAL.

### INC002 — Fan-out excesivo de módulo

**Qué detecta:** módulos que incluyen más headers locales distintos que el umbral configurado.

**Por qué importa:** el fan-out (acoplamiento eferente) de un módulo determina cuántos otros módulos pueden afectarlo. Un módulo con fan-out alto es frágil: un cambio en cualquiera de sus dependencias puede requerir que sea revisado, recompilado y retesteado. En sistemas embebidos donde la trazabilidad de cambios es un requisito de los estándares de seguridad funcional, el fan-out alto aumenta el alcance de impacto de cada modificación.

**Umbral por defecto:** 12 includes locales distintos. En proyectos con certificación estricta se usa 5–8.

**Severidad:** CRITICAL.

### LAY001 — Violación de capa IEC 62304

**Qué detecta:** includes que cruzan la jerarquía de capas en dirección no permitida. Ejemplo con la jerarquía `platform → hal → app`: un archivo de la capa `hal` que incluye un header de la capa `app` viola la regla porque `app` no está en las dependencias permitidas de `hal`.

**Por qué importa:** IEC 62304 (software de dispositivos médicos) y otros estándares de seguridad funcional exigen que la arquitectura de software esté organizada en capas con dependencias unidireccionales. Esta restricción asegura que los módulos de nivel inferior (drivers, HAL) no tengan dependencias de módulos de nivel superior (lógica de aplicación), lo que facilita la reutilización, el testing aislado y el análisis de impacto de cambios.

Una violación de capa suele indicar uno de dos problemas: o el módulo de nivel bajo está asumiendo responsabilidades que pertenecen a un nivel superior, o la arquitectura de capas no fue respetada durante el desarrollo. Ambos casos requieren corrección antes del merge.

**Severidad:** CRITICAL.

---

## Clasificación de severidades

| Severidad | Color | Significado operativo |
|---|---|---|
| CRITICAL | rojo intenso | Violación de diseño o arquitectura. Bloquea el merge (exit code 1). |
| WARNING | amarillo | No utilizado en la versión actual. Reservado para checks futuros. |
| INFO | cyan | No utilizado en la versión actual. Reservado para checks futuros. |

DesignReviewer-C retorna **exit code 1** si hay al menos un finding CRITICAL, y **exit code 0** si el análisis no produce findings o solo produce findings de menor severidad.

---

## Limitaciones conocidas

**Resolución de includes relativa al archivo fuente:** el analyzer resuelve rutas de include relativas al directorio del archivo que las contiene. Rutas que usan variables del preprocesador o que dependen de `-I` flags del compilador no se pueden resolver sin información del sistema de build.

**Un include por referencia de path:** la detección de capa se basa en los componentes del path. Si un proyecto organiza sus capas de una forma no jerárquica en el sistema de archivos (ej. todos los archivos en un directorio plano con prefijos de nombre), la detección no funcionará correctamente. La organización en subdirectorios por capa es un prerrequisito.

**Análisis textual sin macros:** el regex que extrae includes no expande macros. Un include como `#include HEADER_FILE` donde `HEADER_FILE` es una macro no será detectado.

**Sin análisis de headers de sistema:** los includes de la forma `#include <stdio.h>` son ignorados completamente. El fan-out y los ciclos solo consideran dependencias locales del proyecto.
