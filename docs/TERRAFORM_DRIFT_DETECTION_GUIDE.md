# Terraform Drift Detection - Guía de Implementación

## Tabla de Contenidos
- [Descripción](#descripción)
- [Características](#características)
- [Cómo Funciona](#cómo-funciona)
- [Requisitos](#requisitos)
- [Configuración](#configuración)
- [Implementación en Otros Repositorios](#implementación-en-otros-repositorios)
- [Secrets Requeridos](#secrets-requeridos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Personalización](#personalización)
- [Troubleshooting](#troubleshooting)

---

## Descripción

La **Terraform Drift Detection Action** es un workflow de GitHub Actions que monitorea automáticamente tu infraestructura de Terraform para detectar cambios no gestionados (drift) entre el estado deseado definido en el código y el estado real en la nube.

### ¿Qué es el Drift?

El **drift** ocurre cuando la infraestructura real difiere del estado definido en Terraform, generalmente debido a:
- Cambios manuales realizados directamente en la consola de AWS/Azure/GCP
- Modificaciones realizadas por otros sistemas o scripts
- Eliminación o creación de recursos fuera de Terraform
- Cambios en configuraciones por parte de otros equipos

---

## Características

- **Monitoreo Automático**: Ejecución programada diaria (6 AM UTC)
- **Ejecución Manual**: Trigger manual con selección de ambiente específico
- **Multi-Environment**: Soporte para múltiples ambientes (dev, staging, prod)
- **Multi-Workspace**: Detecta drift en todos los workspaces de Terraform
- **Notificaciones Inteligentes**:
  - Creación automática de GitHub Issues con el detalle del drift
  - Prevención de duplicados mediante hashing de contenido
  - Integración opcional con Microsoft Teams
- **Detalle Completo**: Incluye el plan completo de Terraform en formato diff
- **Manejo de Errores Robusto**: Continúa procesando otros ambientes si uno falla

---

## Cómo Funciona

### Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│  1. Trigger (Schedule o Manual)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Autenticación AWS (OIDC)                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Inicialización de Terraform                              │
│     - terraform init con backend S3                          │
│     - Configuración de región y bucket                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Listado de Workspaces                                    │
│     - terraform workspace list                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Para cada workspace:                                     │
│     ┌─────────────────────────────────────────────────┐     │
│     │ 5.1 terraform plan -detailed-exitcode           │     │
│     └───────────────┬─────────────────────────────────┘     │
│                     │                                        │
│     ┌───────────────▼─────────────────────────────────┐     │
│     │ Exit Code 0: No changes                         │     │
│     │ Exit Code 1: Error (continúa)                   │     │
│     │ Exit Code 2: DRIFT DETECTADO ───────────────┐   │     │
│     └─────────────────────────────────────────────│───┘     │
│                                                   │          │
│                     ┌─────────────────────────────▼───┐     │
│                     │ 5.2 Generar hash del plan       │     │
│                     └─────────────────┬───────────────┘     │
│                                       │                      │
│                     ┌─────────────────▼───────────────┐     │
│                     │ 5.3 ¿Issue existente con hash?  │     │
│                     └─────┬───────────────┬───────────┘     │
│                           │ Sí            │ No               │
│                           ▼               ▼                  │
│                     ┌──────────┐   ┌──────────────────┐     │
│                     │  Skip    │   │ Crear Issue      │     │
│                     └──────────┘   │ + Agregar Labels │     │
│                                    │ + Notificar Teams│     │
│                                    └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Códigos de Salida de Terraform Plan

| Exit Code | Significado | Acción |
|-----------|-------------|---------|
| `0` | No hay cambios | Continúa al siguiente workspace |
| `1` | Error en Terraform | Registra error y continúa |
| `2` | Cambios detectados (DRIFT) | Crea issue y notificación |

### Prevención de Duplicados

El sistema genera un hash SHA-256 único de los primeros 8 caracteres basado en el contenido del plan. Si ya existe un issue abierto con el mismo hash en el título, no se crea uno nuevo, evitando spam.

---

## Requisitos

### 1. GitHub Repository
- Permisos de escritura en Issues
- GitHub Actions habilitado

### 2. AWS
- Cuenta de AWS configurada
- IAM Role con permisos para:
  - Leer el estado de Terraform desde S3
  - Ejecutar `terraform plan` sobre los recursos gestionados
- OIDC configurado entre GitHub Actions y AWS (recomendado)

### 3. Terraform
- Versión compatible (configurada en el workflow, por defecto 1.6.0)
- Backend configurado en S3
- Workspaces creados

### 4. Estructura del Proyecto
```
repository/
├── .github/
│   └── workflows/
│       └── terraform-drift-detection.yml
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── ...
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
└── docs/
    └── TERRAFORM_DRIFT_DETECTION_GUIDE.md
```

---

## Configuración

### Paso 1: Configurar OIDC en AWS (Recomendado)

Para configurar autenticación sin credenciales de larga duración:

1. **Crear OIDC Provider en AWS**:
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

2. **Crear IAM Role con Trust Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

3. **Agregar Permisos de Terraform**:
Adjunta políticas según los recursos que gestiona tu Terraform (EC2, S3, RDS, etc.)

### Paso 2: Configurar Backend de Terraform

Asegúrate de que tu configuración de Terraform use S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "dev/terraform.tfstate"
    region = "us-east-1"
  }
}
```

---

## Implementación en Otros Repositorios

### Paso 1: Copiar el Workflow

Copia el archivo `.github/workflows/terraform-drift-detection.yml` a tu repositorio en la misma ubicación.

### Paso 2: Ajustar Variables de Entorno

Edita el workflow según tus necesidades:

```yaml
env:
  TF_VERSION: '1.6.0'  # Versión de Terraform
  AWS_REGION: ${{ secrets.AWS_REGION }}
```

### Paso 3: Configurar Environments en GitHub

1. Ve a **Settings** → **Environments** en tu repositorio
2. Crea un environment llamado `DEV` (o el nombre que uses)
3. Configura los secrets necesarios

### Paso 4: Configurar Secrets

Ve a **Settings** → **Secrets and variables** → **Actions** y agrega:

#### Secrets Obligatorios:
- `AWS_REGION`: Región de AWS (ej: `us-east-1`)
- `AWS_ROLE_ARN`: ARN del rol de IAM para OIDC (ej: `arn:aws:iam::123456789012:role/GitHubActionsRole`)
- `TF_STATE_BUCKET`: Nombre del bucket S3 con el estado de Terraform
- `TF_STATE_KEY`: Path del archivo de estado (ej: `terraform.tfstate`)
- `GH_TOKEN`: Token de GitHub con permisos para crear issues
  - Scopes necesarios: `repo` (issues write)
  - Crear en: **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**

#### Secrets Opcionales:
- `TEAMS_WEBHOOK_URL`: URL del webhook de Microsoft Teams para notificaciones

### Paso 5: Ajustar Estructura de Directorios

Si tu estructura de directorios es diferente, modifica la línea:

```yaml
cd environments/${{ github.event.inputs.environment || 'dev' }}
```

Por ejemplo, si tus ambientes están en `terraform/envs/`:
```yaml
cd terraform/envs/${{ github.event.inputs.environment || 'dev' }}
```

### Paso 6: Personalizar Schedule

Cambia el cron para ajustar la frecuencia de ejecución:

```yaml
schedule:
  - cron: '0 6 * * *'  # Diario a las 6 AM UTC
```

Ejemplos:
- `'0 */6 * * *'` - Cada 6 horas
- `'0 9 * * 1-5'` - Lunes a viernes a las 9 AM
- `'0 0 * * 0'` - Sólo domingos a medianoche

### Paso 7: Probar el Workflow

1. **Ejecución Manual**:
   - Ve a **Actions** → **Terraform Drift Detection**
   - Click en **Run workflow**
   - Selecciona el ambiente
   - Click en **Run workflow**

2. **Verificar Logs**:
   - Revisa los logs de ejecución
   - Verifica que la autenticación AWS funcione
   - Confirma que Terraform se inicializa correctamente

3. **Crear Drift de Prueba**:
   - Haz un cambio manual en AWS (ej: agregar un tag a un recurso)
   - Ejecuta el workflow manualmente
   - Verifica que se cree un issue con el drift detectado

---

## Secrets Requeridos

### Resumen de Secrets

| Secret | Tipo | Descripción | Ejemplo |
|--------|------|-------------|---------|
| `AWS_REGION` | Obligatorio | Región de AWS | `us-east-1` |
| `AWS_ROLE_ARN` | Obligatorio | ARN del IAM Role para OIDC | `arn:aws:iam::123456789012:role/GHActionsRole` |
| `TF_STATE_BUCKET` | Obligatorio | Bucket S3 del estado de Terraform | `my-terraform-state` |
| `TF_STATE_KEY` | Obligatorio | Path del estado en S3 | `terraform.tfstate` |
| `GH_TOKEN` | Obligatorio | Token de GitHub para crear issues | `ghp_xxxxxxxxxxxx` |
| `TEAMS_WEBHOOK_URL` | Opcional | Webhook de Microsoft Teams | `https://outlook.office.com/webhook/...` |

### Cómo Crear GH_TOKEN

1. Ve a GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Click en **Generate new token**
3. Nombre: `Terraform Drift Detection`
4. Expiration: Elige según tus políticas
5. Repository access: Selecciona el repositorio
6. Permissions:
   - **Issues**: Read and write
   - **Contents**: Read (opcional, para checkout)
7. Click **Generate token**
8. Copia el token y guárdalo en los secrets del repositorio

### Cómo Crear TEAMS_WEBHOOK_URL

1. En Microsoft Teams, ve al canal donde quieres las notificaciones
2. Click en **⋯** → **Connectors**
3. Busca **Incoming Webhook** y click **Configure**
4. Dale un nombre: `Terraform Drift Alerts`
5. Opcionalmente sube una imagen
6. Click **Create**
7. Copia la URL del webhook
8. Guárdala en los secrets del repositorio

---

## Estructura del Proyecto

### Configuración Recomendada

```
terraform-project/
├── .github/
│   └── workflows/
│       └── terraform-drift-detection.yml
│
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
│
├── modules/
│   ├── networking/
│   ├── compute/
│   └── storage/
│
├── docs/
│   ├── TERRAFORM_DRIFT_DETECTION_GUIDE.md
│   └── ARCHITECTURE.md
│
├── CHANGELOG.md
└── README.md
```

### Workspaces vs Directorios

El workflow soporta **ambos enfoques**:

#### Opción 1: Directorios Separados (Recomendado)
```
environments/
├── dev/
├── staging/
└── prod/
```

Ventajas:
- Clara separación de configuraciones
- Más fácil de gestionar para diferentes equipos
- Menos riesgo de aplicar cambios al ambiente equivocado

#### Opción 2: Workspaces de Terraform
```
environments/
└── shared/
    └── main.tf  # Usa terraform workspaces: dev, staging, prod
```

Ventajas:
- Menos duplicación de código
- Útil cuando las configuraciones son muy similares

El workflow detecta automáticamente todos los workspaces disponibles con:
```bash
terraform workspace list
```

---

## Personalización

### Cambiar Formato de Issues

Edita la sección donde se crea el body del issue:

```bash
# Formato actual (diff)
echo '```diff' > "${ISSUE_BODY}"
terraform show -no-color "${PLAN}" >> "${ISSUE_BODY}"
echo '```' >> "${ISSUE_BODY}"
```

Puedes agregar más contexto:
```bash
cat <<EOF > "${ISSUE_BODY}"
## Drift Detectado en ${workspace}

**Fecha**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Branch**: ${GITHUB_REF#refs/heads/}
**Commit**: ${GITHUB_SHA:0:7}

### Cambios Detectados

\`\`\`diff
$(terraform show -no-color "${PLAN}")
\`\`\`

### Próximos Pasos

1. Revisar los cambios detectados
2. Determinar si son esperados o no
3. Si son cambios manuales no deseados, ejecutar \`terraform apply\` para corregir
4. Si son cambios esperados, actualizar el código de Terraform

---
*Generado automáticamente por Terraform Drift Detection*
EOF
```

### Agregar Más Notificaciones

Puedes agregar notificaciones a Slack, Discord, Email, etc.

**Ejemplo Slack**:
```yaml
- name: Send Slack Notification
  if: env.DRIFT_DETECTED == 'true'
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Drift detectado en ${{ matrix.environment }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": ":warning: *Drift Detectado*\n*Ambiente:* ${{ matrix.environment }}\n*Repo:* ${{ github.repository }}"
            }
          }
        ]
      }
```

### Filtrar Workspaces Específicos

Si no quieres monitorear todos los workspaces, filtra la lista:

```bash
# Excluir workspace "test"
terraform workspace list | sed 's/^[ *]*//;/^$/d' | grep -v "test" > workspaces.txt

# Solo workspaces de producción
terraform workspace list | sed 's/^[ *]*//;/^$/d' | grep "prod" > workspaces.txt
```

### Ejecutar en Múltiples Ambientes en Paralelo

Usa matrix strategy:

```yaml
jobs:
  terraform-drift-detection:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]
    environment: ${{ matrix.environment }}
    steps:
      # ... resto del workflow
```

---

## Troubleshooting

### Problema: Issues no se crean

**Síntomas**: El workflow detecta drift pero no aparecen issues

**Soluciones**:
1. Verifica que `GH_TOKEN` tenga permisos de `issues: write`
2. Verifica que el workflow tenga `permissions.issues: write`
3. Revisa los logs para ver el error específico:
   ```
   ❌ Error creating issue: <mensaje de error>
   ```

### Problema: Error de autenticación AWS

**Síntomas**:
```
Error: Unable to locate credentials
```

**Soluciones**:
1. Verifica que `AWS_ROLE_ARN` sea correcto
2. Confirma que el OIDC provider esté configurado en AWS
3. Revisa el Trust Policy del IAM Role
4. Verifica que el repositorio en la condición coincida

### Problema: Terraform init falla

**Síntomas**:
```
Error: Failed to get existing workspaces
```

**Soluciones**:
1. Verifica que `TF_STATE_BUCKET` exista y sea accesible
2. Confirma que el IAM Role tenga permisos de S3:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:ListBucket`
3. Verifica que el backend esté correctamente configurado

### Problema: Labels no se agregan a los issues

**Síntomas**: Issues se crean pero sin labels

**Esto es esperado**: El workflow hace el intento de agregar labels de forma no-bloqueante. Si los labels no existen en el repositorio, simplemente no se agregan.

**Solución opcional**:
Crea los labels manualmente:
1. Ve a **Issues** → **Labels**
2. Crea:
   - `terraform` (color: #844FBA)
   - `drift-detection` (color: #FF6B6B)
   - `infrastructure` (color: #0E8A16)

### Problema: Demasiados issues duplicados

**Síntomas**: Se crean múltiples issues para el mismo drift

**Causa**: El contenido del plan varía ligeramente (timestamps, etc.)

**Solución**: Modifica la generación del hash para excluir elementos variables:

```bash
# Excluir timestamps y valores dinámicos antes de hashear
terraform show -no-color "${PLAN}" | \
  sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9:]\+Z/<timestamp>/g' | \
  sha256sum | cut -d' ' -f1 | head -c 8
```

### Problema: Workflow tarda mucho tiempo

**Síntomas**: El workflow toma más de 10-15 minutos

**Soluciones**:
1. **Paralelizar ambientes**: Usa matrix strategy
2. **Cachear Terraform**:
   ```yaml
   - name: Cache Terraform
     uses: actions/cache@v3
     with:
       path: |
         ~/.terraform.d/plugin-cache
       key: ${{ runner.os }}-terraform-${{ hashFiles('**/.terraform.lock.hcl') }}
   ```
3. **Limitar workspaces**: Filtra solo los críticos
4. **Optimizar terraform plan**: Usa `-refresh=false` si el estado está reciente

### Problema: Teams notification falla

**Síntomas**: Issue se crea pero no llega notificación a Teams

**Soluciones**:
1. Verifica que el webhook de Teams esté activo
2. Prueba el webhook manualmente:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"text": "Test message"}' \
     YOUR_TEAMS_WEBHOOK_URL
   ```
3. Verifica que el connector esté habilitado en el canal de Teams

---

## Mejores Prácticas

### 1. Gestión de Issues
- **Cerrar issues resueltos**: Cuando corrijas un drift, cierra el issue manualmente
- **Usar Projects**: Crea un GitHub Project para trackear todos los drifts
- **Asignar responsables**: Usa CODEOWNERS para auto-asignar issues

### 2. Seguridad
- **Rotar tokens**: Rota `GH_TOKEN` periódicamente
- **Usar OIDC**: Evita credenciales de larga duración
- **Limitar permisos**: Da solo los permisos mínimos necesarios al IAM Role
- **Protected branches**: Protege el branch main para evitar cambios no autorizados

### 3. Monitoreo
- **Dashboard**: Crea un dashboard con métricas de drift
- **Alertas**: Configura alertas para drift en producción
- **Revisión regular**: Revisa los issues de drift semanalmente

### 4. Documentación
- **Documentar cambios esperados**: Si haces cambios manuales intencionales, documéntalos
- **Runbooks**: Crea runbooks para tipos comunes de drift
- **Post-mortems**: Documenta incidentes de drift crítico

---

## Ejemplo de Uso

### Escenario: Detectar y Corregir Drift

1. **El workflow detecta drift** (automáticamente a las 6 AM):
   ```
   ⚠️ Changes found in environment 'prod'
   ```

2. **Se crea un issue automáticamente**:
   ```
   Title: Drift detected in environment: prod (a3f7c891)

   Body:
   ```diff
   + aws_instance.web_server:
   +   tags = {
   +     "ManagedBy" = "DevOps Team"  # <- Cambio manual
   +   }
   ```

3. **Recibes notificación en Teams**:
   ```
   Changes detected in infrastructure for environment prod
   ```

4. **Investigas el cambio**:
   - Revisas el issue
   - Determinas que fue un cambio manual no autorizado

5. **Corriges el drift**:
   ```bash
   cd environments/prod
   terraform apply  # Esto revertirá el cambio manual
   ```

6. **Verificas**:
   - Ejecuta el workflow manualmente
   - Confirma que ya no hay drift
   - Cierra el issue

---

## Recursos Adicionales

- [Terraform Documentation](https://www.terraform.io/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS IAM OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [Keep a Changelog](https://keepachangelog.com/)

---

## Soporte

Para problemas o preguntas:
1. Revisa esta guía completa
2. Consulta los logs del workflow en GitHub Actions
3. Revisa el CHANGELOG.md para cambios recientes
4. Abre un issue en el repositorio describiendo el problema

---

## Licencia

Este workflow es de código abierto y puede ser usado, modificado y distribuido libremente.

---

**Última actualización**: 2025-12-04
**Versión del workflow**: 1.1.0
