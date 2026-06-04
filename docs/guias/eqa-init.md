# eqa-init — Guía de usuario

## Instalación

```bash
pip install eqa-framework
```

Verificar que está disponible:

```bash
eqa-init --help
```

---

## Uso básico

### Modo interactivo (recomendado)

Ejecutar en la raíz del proyecto C:

```bash
eqa-init .
```

El comando:
1. Escanea los subdirectorios buscando candidatos a capa.
2. Abre una TUI para ordenar y confirmar la jerarquía.
3. Escribe `pyproject.toml` con las tres secciones de eqa-framework.

### Modo no interactivo

Para entornos sin terminal interactiva (CI, scripts, Docker):

```bash
eqa-init . --no-interactive
```

Escribe el archivo con defaults estándar. La sección `[tool.designreviewer-c.layers]` queda con un comentario `# TODO` para completar manualmente.

### Especificar el directorio de fuentes

Si los fuentes no están en `src/` sino en otro directorio:

```bash
eqa-init . --src-dir firmware
eqa-init . --src-dir core/src
```

Sin `--src-dir`, el comando busca `src/` automáticamente. Si no existe, escanea la raíz del proyecto.

---

## La TUI de jerarquía de capas

```
 eqa-init — Jerarquía de capas
 ─────────────────────────────────────────────────────────────
 Ordenar de menor a mayor nivel. [shift+↑↓] mover · [A] agregar · [X] eliminar · [Enter] confirmar · [Q] cancelar

  #   Capa
  ─   ────────
  1   platform
  2   hal
  3   drivers
  4   app
```

**Cómo usarla:**

- Las capas detectadas aparecen ordenadas alfabéticamente como punto de partida.
- Reordenar con `Shift+↑` y `Shift+↓` para definir la jerarquía de menor a mayor nivel (la capa 1 es la más baja, sin dependencias).
- `A` para agregar una capa que no fue detectada automáticamente.
- `X` para eliminar una capa que no corresponde al proyecto.
- `Enter` para confirmar y escribir el archivo.
- `Q` o `Esc` para cancelar sin escribir nada.

---

## Resultado generado

Después de confirmar con la jerarquía `platform → hal → drivers → app`, el comando genera:

```toml
[tool.codeguard-c]
max_cyclomatic_complexity = 10   # WARNING si CCN supera este valor
max_function_lines        = 50   # WARNING si la función supera este número de líneas
exclude_patterns          = ["build/", "third_party/"]

[tool.codeguard-c.checks]
misra_mandatory = true
misra_required  = true
misra_advisory  = false
security        = true
complexity      = true

[tool.designreviewer-c]
max_fan_out      = 12   # WARNING si un módulo incluye más headers locales distintos
exclude_patterns = ["build/", "third_party/"]

[tool.designreviewer-c.layers]
platform = []
hal      = ["platform"]
drivers  = ["platform"]
app      = ["platform", "hal", "drivers"]

[tool.architectanalyst-c]
max_instability       = 0.8   # WARNING si I = Ce/(Ca+Ce) supera este umbral
max_distance_warning  = 0.3   # WARNING si D = |A+I-1| supera este umbral
max_distance_critical = 0.5   # CRITICAL si D supera este umbral (Zone of Pain/Uselessness)
db_path               = ".quality_control/architecture.db"
exclude_patterns      = ["build/", "third_party/"]
```

---

## Comportamiento con pyproject.toml existente

Si el proyecto ya tiene `pyproject.toml` (por ejemplo, es un monorepo Python/C), `eqa-init` agrega solo las secciones que faltan sin tocar el resto del archivo:

```bash
# Antes
[project]
name = "mi-firmware"
version = "1.0.0"

# Después de eqa-init . --no-interactive
[project]
name = "mi-firmware"
version = "1.0.0"

[tool.codeguard-c]
...
```

Si las tres secciones ya están presentes, el comando informa que no hay cambios y no modifica el archivo:

```
Sin cambios: todas las secciones de eqa-framework ya estaban en pyproject.toml.
```

---

## Casos de uso habituales

### Incorporar eqa-framework a un proyecto nuevo

```bash
cd /path/to/mi-proyecto-c
eqa-init .
# → TUI para definir capas → pyproject.toml generado
codeguard-c src/
```

### Onboarding en CI sin terminal interactiva

```bash
eqa-init . --no-interactive
# Editar manualmente [tool.designreviewer-c.layers] antes de correr designreviewer-c
```

### Proyecto con fuentes en directorio no estándar

```bash
eqa-init /path/to/proyecto --src-dir core
```

### Regenerar una sección eliminada accidentalmente

Si se borró por error `[tool.architectanalyst-c]` del `pyproject.toml`:

```bash
eqa-init . --no-interactive
# Solo agrega la sección faltante; codeguard-c y designreviewer-c no se tocan
```

---

## Preguntas frecuentes

**¿Qué pasa si cancelo la TUI?**
El comando imprime "Cancelado. No se escribió ningún archivo." y sale con exit code 0. El `pyproject.toml` no se modifica.

**¿Puedo correr `eqa-init` varias veces en el mismo proyecto?**
Sí. Solo agrega las secciones que faltan. Si todas ya existen, no hace nada. No hay riesgo de duplicar configuración.

**¿La jerarquía generada es definitiva?**
No. El `pyproject.toml` generado es un punto de partida. La sección `[tool.designreviewer-c.layers]` en particular suele necesitar ajuste manual para reflejar con exactitud las dependencias permitidas entre capas del proyecto.

**¿Qué pasa si mi proyecto no tiene subdirectorios (todo en la raíz)?**
El scanner informa que no detectó candidatos. La TUI abre igualmente con la lista vacía — el usuario puede agregar las capas manualmente con `A`. Con `--no-interactive`, la sección de capas queda con el comentario `# TODO`.

**¿`eqa-init` necesita cppcheck instalado?**
No. `eqa-init` solo genera configuración. Las herramientas de sistema (cppcheck, flawfinder, lizard) son necesarias para correr `codeguard-c`, no para inicializar la configuración.

**¿Puedo usar `eqa-init` con `.embedded-qa.toml` en lugar de `pyproject.toml`?**
No actualmente. `eqa-init` solo escribe en `pyproject.toml`. Si el proyecto usa `.embedded-qa.toml`, copiar el contenido generado manualmente a ese archivo.
