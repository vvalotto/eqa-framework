# eqa-config — Guía de usuario

## Instalación

```bash
pip install eqa-framework
```

Verificar que está disponible:

```bash
eqa-config --help
```

Si el comando no está disponible pero el paquete está instalado, ejecutarlo directamente:

```bash
python -m eqa_framework.config_editor.app
```

---

## Para qué sirve

Los tres agentes (`codeguard-c`, `designreviewer-c`, `architectanalyst-c`) leen su configuración desde el `pyproject.toml` del proyecto. Esa configuración es compartida por todo el equipo y vive en el repositorio.

`eqa-config` permite a **cada desarrollador** sobreescribir cualquier umbral a nivel personal, sin tocar el repositorio. Los valores personales se guardan en `~/.config/eqa/config.toml` y son invisibles para el resto del equipo.

**Casos de uso típicos:**
- Ser más estricto que el proyecto (bajar `max_cyclomatic_complexity` de 12 a 8)
- Ser más permisivo temporalmente mientras se refactoriza
- Probar diferentes umbrales de arquitectura sin commitear

---

## Uso

Lanzar la TUI desde el directorio del proyecto:

```bash
eqa-config
```

Si hay un `pyproject.toml` en el directorio actual (o en algún directorio padre), la columna **Proyecto** mostrará los valores configurados para el equipo. La columna **Personal** muestra tus overrides. La columna **Efectivo** es lo que usarán los agentes al ejecutarse.

---

## Navegación

```
┌────────────────────────────────────────────────────────────────────┐
│ eqa-config — Editor de configuración personal                      │
├──────────────────┬─────────────────────────┬───────┬──────┬───────┤
│ Agente           │ Clave                   │Default│Proy. │Person.│Efectivo│
├──────────────────┼─────────────────────────┼───────┼──────┼───────┤
│ codeguard-c      │ max_cyclomatic_comple.. │ 10    │ 12   │ 8     │ 8   │
│ codeguard-c      │ max_function_lines      │ 50    │ 50   │ —     │ 50  │
│ codeguard-c      │ misra_mandatory         │ True  │ —    │ —     │True │
│ ...              │ ...                     │ ...   │ ...  │ ...   │ ... │
└──────────────────┴─────────────────────────┴───────┴──────┴───────┘
 E Editar  D Borrar personal  S Guardar  Q Salir
```

| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Navegar entre keys |
| `E` o `Enter` | Editar el valor personal de la key seleccionada |
| `D` | Borrar tu valor personal para esa key (vuelve al valor del proyecto o default) |
| `S` | Guardar todos los cambios en `~/.config/eqa/config.toml` |
| `Q` | Salir — pide confirmación si hay cambios sin guardar |

---

## Editar un valor

1. Navegar con `↑`/`↓` hasta la key deseada
2. Pulsar `E` — aparece un modal con el valor actual
3. Escribir el nuevo valor y pulsar `Enter`
4. Si el valor no es válido para el tipo (por ejemplo, texto donde va un número), aparece un error y el modal se cierra sin cambiar nada
5. Pulsar `S` para guardar

**Formato según tipo:**

| Tipo | Ejemplos válidos |
|------|-----------------|
| `int` | `8`, `12`, `50` |
| `float` | `0.6`, `0.8`, `1.0` |
| `bool` | `true`, `false`, `yes`, `no`, `1`, `0` |
| `str` | cualquier texto |

---

## Ejemplo: ajustar umbrales de CodeGuard-C

Supón que el proyecto tiene `max_cyclomatic_complexity = 12` pero querés trabajar con un umbral más estricto de 8:

1. Abrir `eqa-config`
2. Navegar a la fila `codeguard-c / max_cyclomatic_complexity`
3. Pulsar `E`, escribir `8`, `Enter`
4. Pulsar `S` para guardar

Desde ese momento, cuando ejecutes `codeguard-c src/`, usará 8 como umbral aunque el `pyproject.toml` diga 12.

---

## Resetear un valor personal

Para volver al valor del proyecto (o al default si no hay valor de proyecto):

1. Navegar a la fila
2. Pulsar `D`

El valor en la columna **Personal** pasa a `—` y **Efectivo** vuelve al valor del proyecto o default.

---

## El archivo de configuración personal

`eqa-config` guarda los cambios en `~/.config/eqa/config.toml`. Podés editar ese archivo directamente con cualquier editor de texto:

```toml
[codeguard-c]
max_cyclomatic_complexity = 8

[designreviewer-c]
max_nesting_depth = 3

[architectanalyst-c]
max_instability = 0.6
```

Solo se guardan los valores que difieren del proyecto (o que querés imponer independientemente del proyecto). No hace falta listar todos los keys.

---

## Funcionamiento sin pyproject.toml

`eqa-config` funciona aunque no haya `pyproject.toml` en el directorio actual. En ese caso la columna **Proyecto** muestra `—` para todas las filas y la columna **Efectivo** refleja tu config personal o los defaults.

Útil para configurar valores globales que apliquen a cualquier proyecto.

---

## Propagación a los agentes

Los agentes leen la config personal automáticamente sin ninguna opción adicional. El merge ocurre en `shared/config.load_toml_section()` con `apply_personal=True` (comportamiento por defecto).

Si por algún motivo necesitás que un agente ignore tu config personal, no hay una opción CLI para eso — editá o borrá las entradas con `eqa-config`.
