# Drift Detection Metrics - Guía de Implementación

Esta guía explica cómo implementar el sistema de métricas de Drift Detection en cualquier repositorio de GitHub.

## Descripción

El sistema **Drift Detection Metrics** analiza los issues de drift detectados en tu repositorio y genera un reporte HTML interactivo con:

- Resumen de issues de drift de los últimos 30 días
- Detalle por repositorio (útil para organizaciones)
- Gráfico de timeline con Chart.js
- Exportación automática como artefacto de GitHub Actions

---

## Archivos Necesarios

Para implementar este sistema necesitas copiar **4 archivos** a tu repositorio:

```
tu-repositorio/
├── .github/
│   └── workflows/
│       └── terraform-drift-detection-metrics.yml
├── scripts/
│   ├── github_drift_issues.py
│   └── requirements.txt
└── templates/
    └── drift_report.html
```

---

## Paso 1: Crear el Workflow

Crea el archivo `.github/workflows/terraform-drift-detection-metrics.yml`:

```yaml
name: Terraform Drift Detection Metrics

on:
  schedule:
    # Ejecutar todos los días a las 8:00 AM UTC
    - cron: '0 8 * * *'

  # Permitir ejecución manual desde la interfaz de GitHub
  workflow_dispatch:

jobs:
  drift-detection:
    name: Detectar Issues de Drift
    runs-on: ubuntu-latest
    environment: DEV  # Cambiar al nombre de tu environment

    permissions:
      id-token: write
      contents: read
      issues: write

    steps:
      - name: Checkout código
        uses: actions/checkout@v4

      - name: Configurar Python 3.x
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Instalar dependencias Python
        run: |
          python -m pip install --upgrade pip
          pip install -r scripts/requirements.txt

      - name: Ejecutar detección de drift
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
          GH_URL: ${{ github.server_url }}/${{ github.repository }}
        run: |
          python scripts/github_drift_issues.py

      - name: Subir reporte HTML como artefacto
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: drift-detection-report-${{ github.run_number }}
          path: "*.html"
          retention-days: 30

      - name: Mostrar resumen en logs
        if: always()
        run: |
          echo "### Resumen de Drift Detection" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          if ls *.html 1> /dev/null 2>&1; then
            echo "Reporte HTML generado exitosamente" >> $GITHUB_STEP_SUMMARY
            echo "Revisa los artefactos para descargar el reporte completo" >> $GITHUB_STEP_SUMMARY
          else
            echo "No se encontraron issues de drift en los últimos 30 días" >> $GITHUB_STEP_SUMMARY
          fi
```

---

## Paso 2: Crear el Script Python

Crea el archivo `scripts/github_drift_issues.py`. Este script consulta la API de GitHub para buscar issues con "Drift detected" en el título.

> **Nota**: El script completo está disponible en el repositorio original. Copia el contenido del archivo `scripts/github_drift_issues.py`.

### Funcionalidades del Script

- Consulta la API de Issues de GitHub (no Search API)
- Filtra issues por título que contenga "Drift detected"
- Filtra por rango de fechas (últimos 30 días)
- Genera reporte HTML con template personalizable
- Soporte para repositorios individuales u organizaciones completas

---

## Paso 3: Crear el archivo de dependencias

Crea el archivo `scripts/requirements.txt`:

```
requests
colorama
```

---

## Paso 4: Crear el Template HTML

Crea el archivo `templates/drift_report.html`. Este template define el diseño del reporte generado.

> **Nota**: El template completo está disponible en el repositorio original. Copia el contenido del archivo `templates/drift_report.html`.

El template incluye:
- Estilos CSS integrados (no requiere archivos externos)
- Gráfico de timeline con Chart.js (cargado desde CDN)
- Tabla de issues por repositorio
- Diseño responsive

---

## Paso 5: Configurar GitHub Environment

1. Ve a tu repositorio en GitHub
2. **Settings** → **Environments**
3. Click en **New environment**
4. Nombre: `DEV` (o el nombre que uses en el workflow)
5. Click **Configure environment**

---

## Paso 6: Configurar el Secret GH_TOKEN

El secret `GH_TOKEN` es necesario para consultar la API de GitHub.

### Crear Personal Access Token (PAT)

1. Ve a GitHub → **Settings** (tu perfil personal)
2. **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token** → **Generate new token (classic)**
4. Configura:
   - **Note**: `Drift Detection Metrics`
   - **Expiration**: Según tus políticas de seguridad
   - **Scopes**:
     - `repo` (Full control of private repositories)
5. Click **Generate token**
6. **Copia el token** (solo se muestra una vez)

### Agregar el Secret al Environment

1. Ve a tu repositorio → **Settings** → **Environments** → **DEV**
2. En **Environment secrets**, click **Add secret**
3. **Name**: `GH_TOKEN`
4. **Value**: Pega el token generado
5. Click **Add secret**

---

## Paso 7: Probar el Workflow

### Ejecución Manual

1. Ve a **Actions** en tu repositorio
2. Selecciona **Terraform Drift Detection Metrics**
3. Click **Run workflow**
4. Selecciona el branch (main)
5. Click **Run workflow**

### Verificar Resultados

1. Espera a que el workflow termine
2. Click en el workflow run
3. En **Summary**, baja hasta la sección **Artifacts**
4. Descarga el archivo `drift-detection-report-X`
5. Descomprime y abre el archivo HTML en tu navegador

---

## Configuración Avanzada

### Cambiar el Schedule

Modifica el cron en el workflow:

```yaml
schedule:
  - cron: '0 8 * * *'  # Diario a las 8 AM UTC
```

Ejemplos:
- `'0 */6 * * *'` - Cada 6 horas
- `'0 9 * * 1-5'` - Lunes a viernes a las 9 AM UTC
- `'0 0 * * 0'` - Domingos a medianoche

### Escanear una Organización Completa

Cambia la variable `GH_URL` en el workflow:

```yaml
env:
  GH_TOKEN: ${{ secrets.GH_TOKEN }}
  GH_URL: https://github.com/tu-organizacion
```

El script detectará automáticamente que es una organización y escaneará todos sus repositorios.

### Cambiar el Título de Búsqueda

Si tus issues de drift tienen un título diferente, edita el script `github_drift_issues.py`:

```python
# Buscar en la función query_repo_issues
if 'Drift detected' not in title:  # Cambiar este texto
    continue
```

### Cambiar el Período de Análisis

Por defecto analiza los últimos 30 días. Para cambiarlo, edita el script:

```python
def _set_default_dates(self):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Cambiar 30 por otro valor
```

---

## Troubleshooting

### Error: "Variables de entorno faltantes: GH_TOKEN"

**Causa**: El secret `GH_TOKEN` no está configurado en el environment.

**Solución**:
1. Verifica que el environment exista (Settings → Environments)
2. Verifica que el secret `GH_TOKEN` esté configurado en ese environment
3. Verifica que el nombre del environment en el workflow coincida

### Error: "422 Unprocessable Entity"

**Causa**: El token no tiene permisos suficientes o hay un problema con la API.

**Solución**: El script ya usa la API de Issues en lugar de Search API, que es más permisiva. Si persiste:
1. Regenera el token con permisos `repo` completos
2. Verifica que el token no haya expirado

### Error: "No such file or directory: templates/drift_report.html"

**Causa**: El template HTML no existe o está en la ubicación incorrecta.

**Solución**: Verifica que el archivo esté en `templates/drift_report.html` (relativo a la raíz del repositorio).

### No se detectan issues existentes

**Causas posibles**:
1. Los issues no tienen "Drift detected" en el título
2. Los issues están cerrados (solo busca abiertos)
3. Los issues fueron creados hace más de 30 días

**Solución**: Verifica el título exacto de tus issues de drift y ajusta el script si es necesario.

### El artefacto no se genera

**Causa**: No se encontraron issues de drift en el período.

**Solución**: Esto es comportamiento esperado. El reporte solo se genera si hay issues que mostrar.

---

## Estructura de Archivos Completa

```
tu-repositorio/
├── .github/
│   └── workflows/
│       └── terraform-drift-detection-metrics.yml  # Workflow de GitHub Actions
├── scripts/
│   ├── github_drift_issues.py                     # Script principal (Python)
│   └── requirements.txt                           # Dependencias Python
└── templates/
    └── drift_report.html                          # Template del reporte HTML
```

---

## Resumen de Secrets Requeridos

| Secret | Ubicación | Descripción |
|--------|-----------|-------------|
| `GH_TOKEN` | Environment (DEV) | Personal Access Token con scope `repo` |

---

## Próximos Pasos

Una vez implementado, puedes:

1. **Integrar con el workflow de drift detection**: Ejecutar las métricas automáticamente después de detectar drift
2. **Agregar notificaciones**: Enviar el reporte por email o Slack
3. **Crear dashboard**: Usar los datos para un dashboard de monitoreo
4. **Personalizar el template**: Modificar el HTML/CSS según tu branding

---

## Soporte

Para problemas o preguntas:
1. Revisa la sección de Troubleshooting
2. Verifica los logs del workflow en GitHub Actions
3. Abre un issue en el repositorio original

---

**Última actualización**: 2026-01-22
