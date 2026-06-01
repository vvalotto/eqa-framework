---
name: resume
description: Restaurar contexto de sesión anterior. Usar al inicio de una nueva sesión para retomar el trabajo previo.
disable-model-invocation: false
---

# Restaurar Contexto de Sesión

Restaura y muestra el contexto de la sesión anterior.

## Instrucciones

Cuando este comando es invocado:

### 1. Verificar archivos de sesión

Buscar archivos en `~/.claude/projects/-Users-victor-PycharmProjects-eqa-framework/memory/`:
- `session-metadata.json` - Metadata de la última sesión
- `session-current.md` - Estado actual de la sesión
- `session-history.md` - Historial de sesiones anteriores

Si `session-metadata.json` no existe, informar al usuario:
> "No se encontró sesión anterior. Parece ser un inicio nuevo."

### 2. Leer y parsear los archivos de sesión

Leer los tres archivos para obtener:
- Timestamp y branch de la última sesión
- Razón de salida (normal, error, timeout, etc.)
- **Commits de la última sesión** (capturados automáticamente por el hook SessionEnd al final de session-current.md)
- Qué se completó
- Estado actual y decisiones tomadas
- Próximos pasos y tareas pendientes

**IMPORTANTE:** El hook SessionEnd agrega automáticamente los commits al final de `session-current.md`. Buscar una sección como:
```
## 📝 Sesión Finalizada: YYYY-MM-DD HH:MM
### Commits en esta sesión:
- hash mensaje del commit
```
Estos commits son el indicador PRINCIPAL de lo que se logró en la última sesión.

### 3. Generar resumen completo

**IMPORTANTE: Todo el output DEBE estar en español.**

Mostrar un resumen estructurado:

```markdown
# 📋 Contexto de Sesión Restaurado

**Última Sesión:** <timestamp de metadata>
**Branch:** <git branch de metadata>
**Razón de Salida:** <exit_reason de metadata>

## ✅ Resumen de la Sesión Anterior

<Extraer estado de completado de session-current.md>

## 🔍 Decisiones Clave y Contexto

<Extraer decisiones importantes o contexto>

## 🎯 Estado Actual

<Extraer descripción del estado actual>

## 🚀 Próximas Actividades

<Extraer y listar próximos pasos>

---

**Contexto restaurado exitosamente. Listo para continuar el trabajo.**
```

### 4. Actualizar el tracking de sesión

- Agregar entrada a `session-history.md` documentando la sesión completada (usar commits como evidencia)
- **Resetear `session-current.md`** - Crear template limpio para la nueva sesión:
  ```markdown
  # Sesión Actual - eqa-framework

  ## 📝 Sesión Iniciada: <fecha/hora actual>
  **Branch:** <branch actual>
  **Contexto Restaurado:** ✅ /resume ejecutado

  ### 🎯 Objetivo de Esta Sesión
  <A determinar según próximos pasos>

  ### ✅ Completado
  <Se irá completando a medida que avanza el trabajo>

  ### 🚀 Próximos Pasos
  <A determinar>
  ```
- Eliminar `session-needs-summary.flag` si existe

### 5. Manejo de casos especiales

**Todos los mensajes DEBEN estar en español:**

- **Sin archivo de metadata:** "No se encontró sesión anterior. Parece ser un inicio nuevo."
- **JSON corrupto:** "Error al leer metadata JSON. Intentando recuperar información de archivos .md"
- **Archivos de sesión vacíos:** "Los archivos de sesión existen pero están vacíos. Comenzando de cero."

## Ubicación de Archivos

Todos los archivos de sesión están en:
```
~/.claude/projects/-Users-victor-PycharmProjects-eqa-framework/memory/
├── session-metadata.json
├── session-current.md
├── session-history.md
└── session-needs-summary.flag (opcional)
```

## Tips

- **TODO EL OUTPUT DEBE ESTAR EN ESPAÑOL** - Requisito obligatorio
- Ser conciso pero completo - mostrar lo que importa
- **Usar los commits como fuente primaria de verdad** sobre lo que se logró
- Analizar los mensajes de commit para entender el alcance del trabajo (feat, fix, docs, test, etc.)
- Consultar CLAUDE.md para entender qué debería venir después
- Resaltar cualquier bloqueo o decisión importante
- Si hay tareas pendientes, listarlas claramente
- Siempre limpiar el flag file después de procesarlo
- Resetear session-current.md para preparar la nueva sesión
