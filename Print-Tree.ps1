<#
.SYNOPSIS
    Imprime el árbol de carpetas y archivos de un directorio.

.PARAMETER RootPath
    Ruta raíz desde la que comenzar (por defecto, la carpeta actual).

.EXAMPLE
    .\Print-Tree.ps1 -RootPath "C:\MiProyecto"
#>
param(
    [string]$RootPath = "."
)

function Print-Tree {
    param(
        [string]$Path,
        [string]$Prefix = ""
    )

    # Obtenemos todos los elementos no ocultos y excluimos carpetas específicas
    Get-ChildItem -LiteralPath $Path | Where-Object {
        # No ocultos
        -not ($_.Attributes -band [IO.FileAttributes]::Hidden) -and
        -not ($_.Attributes -band [IO.FileAttributes]::System) -and
        # No carpetas de caché de Python u otras que quieras omitir
        $_.Name -notin ".mypy_cache", "__pycache__", ".ruff_cache" 
    } | ForEach-Object {
        # Imprimimos con prefijo visual
        Write-Output ("{0}|-- {1}" -f $Prefix, $_.Name)

        # Si es directorio, recursión con mayor indentación
        if ($_.PSIsContainer) {
            Print-Tree -Path $_.FullName -Prefix ($Prefix + "|   ")
        }
    }
}

# Resolución de ruta absoluta
$fullPath = (Resolve-Path $RootPath).ProviderPath

# Llamada inicial
Write-Output $fullPath
Print-Tree -Path $fullPath
