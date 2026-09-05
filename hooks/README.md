# Git hooks — Mercadito

Hooks versionados en el repo (no en `.git/hooks/`, que no se puede subir a
git). Se activan una sola vez por clon:

```bash
git config core.hooksPath hooks
```

Después de eso, cada `git commit` corre automáticamente lo que hay en
esta carpeta — no hace falta volver a activarlo salvo que clones el
repo de nuevo en otra máquina.

## Qué hay

- **`pre-commit`** — bloquea el commit si detecta `.env`, `.env.local`
  o variantes (`.env.<algo>.local`) entre los archivos en stage —
  ninguno de esos debe llegar nunca a git, aunque `.gitignore` normalmente
  ya los excluye, esto es una segunda barrera para el caso de un
  `git add -f` por error. También avisa (sin bloquear) si hay archivos
  de más de 5MB en el commit.

## Agregar un hook nuevo

Crear el archivo (sin extension, el nombre es el que espera git:
`pre-commit`, `commit-msg`, `pre-push`, etc.), empezar con `#!/bin/sh`
para que corra igual en Windows (via Git Bash) y en Mac/Linux, y darle
permiso de ejecucion:

```bash
chmod +x hooks/nombre-del-hook
```
