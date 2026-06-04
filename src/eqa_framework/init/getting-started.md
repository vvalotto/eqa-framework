# Guía de instalación y quick start

Esta guía lleva al desarrollador desde cero hasta tener los tres agentes corriendo sobre su proyecto C embebido.

---

## Requisitos previos

### Python

eqa-framework requiere Python 3.11 o superior.

```bash
python3 --version   # Python 3.11.x o superior
```

### cppcheck

El único requisito de sistema. Es obligatorio para `codeguard-c`; los otros dos agentes son Python puro.

```bash
# macOS
brew install cppcheck

# Ubuntu / Debian
sudo apt install cppcheck

# Verificar
cppcheck --version   # Cppcheck 2.x
```

---

## Instalación

```bash
pip install eqa-framework
```

Verifica que los comandos están disponibles:

```bash
eqa-init --help
codeguard-c --help
designreviewer-c --help
architectanalyst-c --help
eqa-config --help
```

---

## Paso 1 — Generar la configuración

Desde la raíz del proyecto C:

```bash
eqa-init .
```

El comando escanea los subdirectorios buscando capas arquitectónicas y abre una TUI:

```
 eqa-init — Jerarquía de capas
 ────────────────────────────────────────────────────────────
 Subdirectorios detectados como posibles capas: app, hal, platform

  #   Capa
  ─   ────────
  1   platform
  2   hal
  3   app
```

Reordenás las capas de menor a mayor nivel con `Shift+↑↓`, confirmás con `Enter`, y el comando escribe `pyproject.toml` en la raíz del proyecto.

### Sin terminal interactiva (CI, Docker)

```bash
eqa-init . --no-interactive
```

Escribe el archivo con defaults estándar. La sección `[tool.designreviewer-c.layers]` queda con un comentario `# TODO` para completar manualmente.

### Si el proyecto ya tiene pyproject.toml

`eqa-init` agrega solo las secciones que faltan sin tocar el contenido existente. Si ya están las tres secciones, no modifica nada.

---

## Paso 2 — Primera corrida: codeguard-c

```bash
codeguard-c src/
```

Analiza todos los `.c` y `.h` bajo `src/` buscando violaciones MISRA-C, funciones inseguras y complejidad excesiva. En la primera corrida en un proyecto existente es normal ver muchos findings — representan el baseline de deuda técnica actual.

```
 File                    Line  Sev       Rule               Message
 src/hal/hal_uart.c        28  CRITICAL  misra-c2012-11.9   misra violation
 src/sensor.c               6  ERROR     FF1014             gets: Does not check for buffer overflows
 src/app/app_logic.c        8  WARNING   CCN001             app_process_sensors: cyclomatic complexity 15

3 CRITICAL · 1 ERROR · 2 WARNING  (2.1s)
```

Para guardar el baseline:

```bash
codeguard-c src/ --format json > baseline.json
```

---

## Paso 3 — Verificar diseño: designreviewer-c

```bash
designreviewer-c src/
echo "Exit code: $?"
```

Detecta dependencias circulares entre headers y violaciones de la jerarquía de capas definida en `pyproject.toml`. Si retorna exit code 1 hay violaciones CRITICAL que deben corregirse.

Si no configuraste capas en el Paso 1, `designreviewer-c` igualmente analiza ciclos y fan-out. La detección de violaciones de capa (LAY001) requiere que `[tool.designreviewer-c.layers]` esté definida.

---

## Paso 4 — Snapshot inicial de arquitectura: architectanalyst-c

```bash
architectanalyst-c src/ --sprint-id baseline
```

Calcula métricas de acoplamiento por módulo (Ca, Ce, I, A, D) y las persiste en SQLite. Las corridas posteriores mostrarán tendencias (↑ ↓ =) respecto a este baseline.

```
 Module        Ca    Ce      I       A       D
 app_logic      2     0   0.00       0.00       1.00
 hal_uart       1     1   0.50       0.00       0.50
 main           0     2   1.00       0.00       0.00

2 CRITICAL · 1 WARNING  (0.3s)
```

---

## Paso 5 (opcional) — Ajustar umbrales personales

Si los umbrales del proyecto son muy estrictos o muy laxos para tu máquina, podés sobreescribirlos sin tocar el `pyproject.toml` del equipo:

```bash
eqa-config
```

Los valores se guardan en `~/.config/eqa/config.toml` y tienen precedencia sobre el proyecto.

---

## Workflow cotidiano

Una vez configurado, el uso día a día es:

| Momento | Comando | Propósito |
|---------|---------|-----------|
| Antes de commitear | `codeguard-c src/` | Detectar defectos nuevos antes de integrar |
| Al abrir un PR | `designreviewer-c src/` | Verificar que el diseño no se degradó |
| Al cerrar el sprint | `architectanalyst-c src/ --sprint-id sprint-XX` | Snapshot arquitectónico con tendencias |

### Generar perfil de calidad Markdown

Cualquier agente puede producir un resumen Markdown para archivar o compartir con el equipo:

```bash
codeguard-c src/ --report reports/codeguard.md
designreviewer-c src/ --report reports/design.md
architectanalyst-c src/ --sprint-id sprint-01 --report reports/arch.md
```

---

## Integración en CI (GitHub Actions)

```yaml
jobs:
  eqa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install system dependencies
        run: sudo apt-get install -y cppcheck

      - name: Install eqa-framework
        run: pip install eqa-framework

      - name: CodeGuard-C
        run: codeguard-c src/

      - name: DesignReviewer-C
        run: designreviewer-c src/
        # Retorna exit code 1 si hay CRITICAL — falla el pipeline automáticamente

      - name: ArchitectAnalyst-C
        run: |
          architectanalyst-c src/ \
            --sprint-id ${{ github.run_number }} \
            --report reports/arch.md

      - name: Upload quality reports
        uses: actions/upload-artifact@v4
        with:
          name: quality-reports
          path: reports/
```

---

## Próximos pasos

- Ajustar umbrales en `pyproject.toml` según el estándar del proyecto (IEC 62304, ISO 26262)
- Definir `[tool.designreviewer-c.layers]` si no se hizo con la TUI
- Configurar `eqa-config` con umbrales personales para el entorno de desarrollo local
- Revisar la documentación técnica de cada agente en `docs/agentes/`
