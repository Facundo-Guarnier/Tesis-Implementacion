### Inicializar Git Pre-Commit:

```bash
git config core.hooksPath .githooks
```

### Ejecutar Pre-commit manualmente:

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File .githooks/pre-commit.ps1
```

**Linux/macOS/WSL:**
```bash
bash .githooks/pre-commit
```
