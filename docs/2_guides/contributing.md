# 🤝 Guía de Contribución

Para mantener la consistencia y la calidad del código, por favor sigue las siguientes guías.

## 🌱 Flujo de Trabajo con Ramas (Branching)

Usamos un modelo de ramas simple pero robusto para organizar el trabajo.

### 🌳 Ramas Principales

- `main`: Contiene la versión estable y de producción del proyecto. Solo se actualiza mediante Pull Requests desde la rama `develop`.
- `develop`: Es la rama de integración principal. Todas las nuevas funcionalidades y correcciones se fusionan aquí antes de pasar a `main`. **Todo el trabajo nuevo debe partir de esta rama.**

### 🌿 Ramas de Trabajo

Cada nueva tarea (funcionalidad, corrección, etc.) debe realizarse en su propia rama. El nombre de la rama debe seguir el formato `tipo/descripcion-corta`.

- **`feature/`**: Para nuevas funcionalidades.
  - _Ejemplo:_ `feature/deteccion-ambulancias`
- **`fix/`**: Para correcciones de errores (bugs).
  - _Ejemplo:_ `fix/error-calculo-tiempos`
- **`docs/`**: Para añadir o mejorar la documentación.
  - _Ejemplo:_ `docs/actualizar-guia-contribucion`
- **`refactor/`**: Para cambios en el código que no añaden funcionalidades ni corrigen errores (ej. mejorar rendimiento, simplificar código).
  - _Ejemplo:_ `refactor/simplificar-clase-detector`

## 📝 Estilo de Commits (Conventional Commits)

Utilizamos el estándar **Conventional Commits** para los mensajes de commit. Esto nos ayuda a mantener un historial claro y nos permite automatizar la generación del `changelog`.

La estructura de un commit es:

```
tipo(ámbito): descripción corta en imperativo
```

- **tipo**: Define la categoría del cambio (ver tabla abajo).
- **(ámbito)**: (Opcional) El módulo o parte del proyecto afectado (ej. `api`, `detector`, `docs`).
- **descripción**: Un resumen claro y conciso de lo que hace el commit.

| Tipo       | Descripción                                                                              |
| ---------- | ---------------------------------------------------------------------------------------- |
| `Feat`     | Una nueva funcionalidad (ej. `feat(api): agregar endpoint de reportes`)                  |
| `Fix`      | Una corrección de un error (ej. `fix(detector): corregir conteo duplicado`)              |
| `Docs`     | Cambios exclusivos en la documentación (ej. `docs: añadir guía de vscode`)               |
| `Style`    | Cambios de formato que no afectan la lógica (ej. `style: aplicar black`)                 |
| `Refactor` | Cambios en el código que no son ni `fix` ni `feat` (ej. `refactor: optimizar bucle`)     |
| `Test`     | Añadir o corregir tests (ej. `test: crear prueba para la lógica de semáforos`)           |
| `Chore`    | Tareas de mantenimiento (ej. `chore: actualizar dependencias en pip`)                    |
| `WIP`      | Trabajo en progreso, no listo para producción (ej. `wip: empezar implementación de API`) |

## 📤 Proceso de Pull Request (PR)

1.  **Sincroniza y crea tu rama:** Asegúrate de tener la última versión de `develop` y crea tu rama de trabajo desde ahí.
    `bash
git checkout develop
git pull origin develop
git checkout -b tipo/tu-descripcion
`
2.  **Trabaja y haz commits:** Realiza tus cambios y haz commits siguiendo el estilo definido.
3.  **Sube tu rama:** `git push -u origin tipo/tu-descripcion`
4.  **Abre un Pull Request:** Ve a GitHub y abre un PR desde tu rama hacia `develop`.
5.  **Describe tu PR:** El título debe ser claro y el cuerpo debe explicar qué cambios hiciste y por qué. Si el PR resuelve una "Issue", enlázala.
6.  **Revisa y fusiona:** Una vez que el PR es aprobado (y las verificaciones automáticas pasan), se fusionará en `develop`.

## 🎨 Estilo y Calidad de Código

Antes de hacer un commit, asegúrate de que tu código cumple con las guías de estilo y calidad definidas en el proyecto. Las herramientas (`ruff`, `black`) configuradas en VS Code deberían ayudarte con esto automáticamente.

- **Guía de estilo de código:** [`./code_style.md`](./code_style.md)
- **Herramientas de calidad:** [`./tooling.md`](./tooling.md)
