# Comando `/pr` - Generador de Descripción de Pull Request

## Descripción
Analiza los commits del branch actual comparado con `main` y genera una descripción de Pull Request **sintética y concisa**.

## Uso
```bash
/pr
```

## Propósito
Generar automáticamente la descripción de un Pull Request analizando los commits del branch actual. El comando produce una descripción estructurada que documenta el **"qué"** y **"por qué"** a alto nivel, sin repetir el detalle de cada commit (que ya está en el historial de git).

## Formato de Salida

### Título del PR
`[Una línea describiendo el cambio principal - max 70 caracteres]`

### Resumen
`[2-3 oraciones máximo explicando QUÉ se logró y POR QUÉ importa]`

### Cambios Principales
- Bullet 1: Categoría/área afectada
- Bullet 2: Otra categoría/área
- Bullet 3: etc.

### Impacto
- Tests: X tests agregados/modificados (total: Y pasando)
- Archivos: X archivos modificados, Y nuevos
- Líneas: ~X líneas agregadas

### Checklist
- [ ] Tests pasando
- [ ] Documentación actualizada (si aplica)

## Comportamiento

El comando ejecuta automáticamente:

1. `git log main..HEAD --oneline` - Para ver commits del branch
2. `git diff main...HEAD --stat` - Para ver archivos modificados
3. Identifica el tema/objetivo PRINCIPAL del PR
4. Genera título y descripción sintética (máximo 10-15 líneas)
5. Muestra la descripción propuesta
6. Pregunta si deseas crear el PR con `gh pr create`

## Principios

- **CONCISO**: Máximo 10-15 líneas en total
- **ALTO NIVEL**: No repite información detallada de cada commit
- **ENFOCADO**: Documenta el "qué" y "por qué", no el "cómo"
- **ESTRUCTURADO**: Formato consistente para facilitar la revisión

## Notas

- Requiere estar en un branch diferente a `main`
- Requiere `gh` CLI instalado y autenticado
