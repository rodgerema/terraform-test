# Adaptación del Drift Detection para Gobierno de Córdoba

## 📋 Resumen Ejecutivo

Este documento analiza las diferencias entre el sistema actual de drift detection y el patrón usado en los proyectos de Gobierno de Córdoba, y propone estrategias de adaptación.

---

## 🔍 Análisis de Diferencias

### 1. Autenticación AWS

| Aspecto | Proyecto Actual | Gobierno de Córdoba |
|---------|-----------------|---------------------|
| **Método** | OIDC (OpenID Connect) | AWS Access Keys + Assume Role |
| **Configuración** | `role-to-assume` | `aws-access-key-id` + `aws-secret-access-key` + `assume_role` en provider |
| **Secretos** | `AWS_ROLE_ARN` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| **Ventaja** | Sin credenciales de larga duración | Compatible con múltiples cuentas |

**Ejemplo actual:**
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ env.AWS_REGION }}
```

**Patrón Gobierno de Córdoba:**
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ inputs.aws_region }}
```

El assume role se hace en el `provider.tf`:
```hcl
provider "aws" {
  region = "us-east-2"
  assume_role {
    role_arn = "arn:aws:iam::243425059285:role/terraform/cbaemprendedora-gitlab-deploy-role"
  }
}
```

### 2. Estructura de Environments

| Aspecto | Proyecto Actual | Gobierno de Córdoba |
|---------|-----------------|---------------------|
| **Naming** | `environments/{env_name}` | `environments/{account_number}` |
| **Ejemplos** | `dev`, `staging`, `prod` | `010836206672` |
| **Variables** | `environment = "dev"` | `cuenta = "010836206672"`, `app_environment = "prod"` |
| **Backend** | `backend.tf` por environment | Backend config en runtime |

### 3. Discovery de Targets

| Aspecto | Proyecto Actual | Gobierno de Córdoba (shared-workflows) |
|---------|-----------------|---------------------------------------|
| **Método** | Terraform workspaces | Escaneo de directorios |
| **Comando** | `terraform workspace list` | `ls -1 environments/` |
| **Output** | Lista de workspaces | Array JSON de directorios |

**Código actual:**
```bash
terraform workspace list | sed 's/^[ *]*//;/^$/d' | grep -E '^[a-zA-Z0-9_-]+$' > workspaces.txt
```

**Patrón shared-workflows:**
```bash
targets=$(ls -1 $TARGETS_DIR/ | jq -R -s -c 'split("\n")[:-1]')
echo "target_array=$targets" >> $GITHUB_OUTPUT
```

### 4. Ejecución de Terraform Plan

| Aspecto | Proyecto Actual | Gobierno de Córdoba |
|---------|-----------------|---------------------|
| **Working Dir** | `environments/{env}` + workspace | `environments/{account_number}` |
| **Init** | Con backend-config en runtime | En cada directorio |
| **Plan** | `terraform plan -detailed-exitcode` | Igual |

---

## 🎯 Estrategias de Adaptación

### Opción A: Workflow Híbrido (Recomendada)

Crear un workflow que detecte automáticamente el patrón a usar:

**Ventajas:**
- Compatible con ambos patrones
- No requiere cambios en proyectos existentes
- Fácil de mantener

**Desventajas:**
- Más complejo
- Necesita lógica de detección

### Opción B: Workflow Separado

Crear un workflow específico para el patrón de Gobierno de Córdoba:

**Ventajas:**
- Más simple y directo
- Enfocado en un solo patrón

**Desventajas:**
- Duplicación de código
- Dos workflows para mantener

### Opción C: Integración con shared-workflows

Reutilizar directamente el workflow compartido de Gobierno de Córdoba:

**Ventajas:**
- Estandarización con el resto de proyectos
- Mantenimiento centralizado

**Desventajas:**
- Menos control sobre la lógica
- Dependencia externa

---

## 📝 Propuesta de Implementación: Opción A (Híbrida)

### Workflow Adaptado: `terraform-drift-detection-hybrid.yml`

```yaml
name: 🔍 Terraform Drift Detection (Hybrid)

on:
  schedule:
    - cron: '0 6 * * *'  # Run daily at 6 AM UTC
  workflow_dispatch:
    inputs:
      discovery_mode:
        description: 'Discovery mode'
        required: true
        default: 'auto'
        type: choice
        options:
          - auto        # Auto-detect
          - workspaces  # Use terraform workspaces
          - directories # Scan directories
      target:
        description: 'Specific target (empty for all)'
        required: false
        type: string
      auth_mode:
        description: 'AWS authentication mode'
        required: true
        default: 'oidc'
        type: choice
        options:
          - oidc        # OpenID Connect (actual)
          - keys        # Access Keys (Gobierno de Córdoba)

env:
  TF_VERSION: '1.6.0'
  AWS_REGION: ${{ secrets.AWS_REGION }}
  TARGETS_DIR: 'environments'

jobs:
  discover:
    name: 'Discover Targets'
    runs-on: ubuntu-latest
    outputs:
      target_array: ${{ steps.get-targets.outputs.target_array }}
      discovery_mode: ${{ steps.get-targets.outputs.discovery_mode }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Discover targets
      id: get-targets
      run: |
        MODE="${{ github.event.inputs.discovery_mode || 'auto' }}"
        TARGET="${{ github.event.inputs.target }}"

        # Si se especificó un target, usarlo directamente
        if [ -n "$TARGET" ]; then
          echo "target_array=[\"$TARGET\"]" >> $GITHUB_OUTPUT
          echo "discovery_mode=manual" >> $GITHUB_OUTPUT
          exit 0
        fi

        # Auto-detectar si no se especificó modo
        if [ "$MODE" = "auto" ]; then
          # Verificar si hay backend.tf en el primer directorio
          FIRST_DIR=$(ls -1 $TARGETS_DIR | head -n 1)
          if [ -f "$TARGETS_DIR/$FIRST_DIR/backend.tf" ]; then
            # Si hay backend.tf, probablemente usa directorios
            MODE="directories"
          else
            # Si no, probablemente usa workspaces
            MODE="workspaces"
          fi
          echo "🔍 Auto-detected mode: $MODE"
        fi

        echo "discovery_mode=$MODE" >> $GITHUB_OUTPUT

        # Descubrir targets según el modo
        if [ "$MODE" = "workspaces" ]; then
          # Método actual: usar primer directorio y listar workspaces
          cd $TARGETS_DIR/dev  # Asume que dev existe
          terraform init -backend=false
          TARGETS=$(terraform workspace list | sed 's/^[ *]*//;/^$/d' | grep -E '^[a-zA-Z0-9_-]+$' | jq -R -s -c 'split("\n")[:-1]')
        else
          # Método Gobierno de Córdoba: escanear directorios
          TARGETS=$(ls -1 $TARGETS_DIR/ | jq -R -s -c 'split("\n")[:-1]')
        fi

        echo "target_array=$TARGETS" >> $GITHUB_OUTPUT
        echo "🎯 Targets discovered: $TARGETS"

  drift-detection:
    name: 'Drift Detection: ${{ matrix.target }}'
    runs-on: ubuntu-latest
    needs: discover

    # Usar diferentes environments según el modo de autenticación
    environment: ${{ github.event.inputs.auth_mode == 'oidc' && 'DEV' || 'production' }}

    permissions:
      id-token: write  # Para OIDC
      contents: read
      issues: write

    strategy:
      fail-fast: false
      matrix:
        target: ${{ fromJson(needs.discover.outputs.target_array) }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    # Paso de autenticación condicional
    - name: 🔧 Configure AWS credentials (OIDC)
      if: github.event.inputs.auth_mode == 'oidc' || github.event.inputs.auth_mode == ''
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: ${{ env.AWS_REGION }}

    - name: 🔧 Configure AWS credentials (Access Keys)
      if: github.event.inputs.auth_mode == 'keys'
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}
        terraform_wrapper: false

    - name: Terraform Drift Detection
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
        TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}
        DISCOVERY_MODE: ${{ needs.discover.outputs.discovery_mode }}
        TARGET: ${{ matrix.target }}
      run: |
        echo "======================================================"
        echo "🚀 Processing target: $TARGET"
        echo "📋 Discovery mode: $DISCOVERY_MODE"
        echo "======================================================"

        # Determinar working directory
        if [ "$DISCOVERY_MODE" = "workspaces" ]; then
          WORK_DIR="$TARGETS_DIR/dev"  # O el primer env que exista
        else
          WORK_DIR="$TARGETS_DIR/$TARGET"
        fi

        cd "$WORK_DIR"

        # Inicializar Terraform
        if [ "$DISCOVERY_MODE" = "workspaces" ]; then
          # Método actual con backend-config
          terraform init -upgrade \
            -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}" \
            -backend-config="key=${TARGET}/${{ secrets.TF_STATE_KEY }}" \
            -backend-config="region=${{ env.AWS_REGION }}"

          # Seleccionar workspace
          terraform workspace select "$TARGET" || terraform workspace new "$TARGET"
        else
          # Método directorios: init simple
          terraform init -upgrade
        fi

        # Ejecutar plan con detailed-exitcode
        PLAN="plan_${TARGET}.tfplan"
        ISSUE_BODY="issue_body_${TARGET}.md"
        ec=0

        echo "Generating plan for target: $TARGET"
        terraform plan -detailed-exitcode -out="$PLAN" 2> /dev/null || ec=$?

        echo "Exit code: $ec"

        case $ec in
          0)
            echo "✅ No changes found in target: $TARGET"
            ;;
          1)
            echo "❌ Terraform command failed in target: $TARGET"
            exit 1
            ;;
          2)
            echo "⚠️ Changes found in target '$TARGET'. Generating notifications..."

            # 1. Create issue body from plan
            echo '```diff' > "${ISSUE_BODY}"
            terraform show -no-color "${PLAN}" >> "${ISSUE_BODY}"
            echo '```' >> "${ISSUE_BODY}"
            sed -i -e 's/  +/+/g' -e 's/  ~/~/g' -e 's/  /-/' "${ISSUE_BODY}"
            MESSAGE=$(cat "${ISSUE_BODY}")

            # 2. Generate unique hash for the message
            UNIQUE_HASH=$(echo -n "${MESSAGE}" | sha256sum | cut -d' ' -f1 | head -c 8)
            ISSUE_TITLE="Drift detected in target: ${TARGET} (${UNIQUE_HASH})"

            echo "Hash: $UNIQUE_HASH"
            echo "Title: $ISSUE_TITLE"

            # 3. Check if issue already exists with this hash
            echo "Checking if issue already exists for this drift..."
            EXISTING_ISSUE=$(gh issue list --state open --search "$UNIQUE_HASH in:title" --json title --jq '.[0].title // empty')

            if [ -n "$EXISTING_ISSUE" ]; then
              echo "⚠️ Drift was already detected previously. No new issue will be created."
              echo "Existing issue found with hash: ${UNIQUE_HASH}"
            else
              echo "Creating GitHub issue for target '$TARGET'..."
              ISSUE_URL=$(gh issue create \
                --title "$ISSUE_TITLE" \
                --body "$MESSAGE" 2>&1)

              if [ $? -eq 0 ]; then
                echo "✅ Issue created successfully: $ISSUE_URL"

                # Try to add labels if they exist (non-blocking)
                echo "Attempting to add labels..."
                gh issue edit "$ISSUE_URL" --add-label "terraform,drift-detection,infrastructure" 2>/dev/null || echo "Labels not added (may not exist in repo)"
              else
                echo "❌ Error creating issue: $ISSUE_URL"
              fi
            fi

            # 4. Send Teams notification
            if [ -n "$TEAMS_WEBHOOK_URL" ]; then
              echo "Creating Teams message..."
              cat <<EOF > payload_teams.json
              {
                "text": "Changes detected in infrastructure for target **${TARGET}** in project **${GITHUB_REPOSITORY}**"
              }
EOF
              curl -X POST -H "Content-Type: application/json" -d @payload_teams.json "$TEAMS_WEBHOOK_URL" || echo "Error sending Teams notification, continuing..."
            else
              echo "Teams webhook URL not defined. Skipping notification."
            fi

            echo "::warning::Terraform drift detected in target: $TARGET"
            ;;
        esac

        echo "======================================================"
        echo "✅ Drift detection completed for target: $TARGET"
        echo "======================================================"
```

---

## 🔧 Cambios en Secretos Necesarios

### Para soportar ambos modos de autenticación:

```yaml
# Secrets existentes (OIDC):
AWS_ROLE_ARN: "arn:aws:iam::123456789012:role/GitHubActionsRole"
AWS_REGION: "us-east-1"
TF_STATE_BUCKET: "terraform-backend-087952009579"
TF_STATE_KEY: "terraform.tfstate"
GH_TOKEN: "ghp_xxxxxxxxxxxx"
TEAMS_WEBHOOK_URL: "https://outlook.office.com/webhook/..."

# Secrets nuevos (Access Keys - Gobierno de Córdoba):
AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

---

## 📦 Opción B: Workflow Separado (Más Simple)

Si prefieres mantener los workflows separados, puedes crear uno nuevo específico para el patrón de Gobierno de Córdoba:

**Archivo:** `.github/workflows/terraform-drift-detection-gcb.yml`

```yaml
name: 🔍 Terraform Drift Detection (Gobierno de Córdoba)

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
    inputs:
      target:
        description: 'Account number (empty for all)'
        required: false
        type: string

env:
  TF_VERSION: '1.6.0'
  AWS_REGION: 'us-east-2'  # Ohio por defecto
  TARGETS_DIR: 'environments'

jobs:
  discover:
    name: 'Discover Account Numbers'
    runs-on: ubuntu-latest
    outputs:
      target_array: ${{ steps.get-targets.outputs.target_array }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Discover account directories
      id: get-targets
      run: |
        if [ -n "${{ github.event.inputs.target }}" ]; then
          echo "target_array=[\"${{ github.event.inputs.target }}\"]" >> $GITHUB_OUTPUT
        else
          TARGETS=$(ls -1 $TARGETS_DIR/ | jq -R -s -c 'split("\n")[:-1]')
          echo "target_array=$TARGETS" >> $GITHUB_OUTPUT
        fi

  drift-detection:
    name: 'Drift: Account ${{ matrix.account }}'
    runs-on: ubuntu-latest
    needs: discover
    environment: production

    permissions:
      contents: read
      issues: write

    strategy:
      fail-fast: false
      matrix:
        account: ${{ fromJson(needs.discover.outputs.target_array) }}

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}
        terraform_wrapper: false

    - name: Terraform Drift Detection
      env:
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
        TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}
        ACCOUNT: ${{ matrix.account }}
      run: |
        cd "$TARGETS_DIR/$ACCOUNT"

        terraform init -upgrade

        PLAN="plan_${ACCOUNT}.tfplan"
        ec=0

        terraform plan -detailed-exitcode -out="$PLAN" || ec=$?

        if [ $ec -eq 2 ]; then
          echo "⚠️ Drift detected in account: $ACCOUNT"

          # Generar issue (misma lógica que el workflow original)
          # ... [código similar al anterior]
        fi
```

---

## 🚀 Pasos de Migración Recomendados

### Fase 1: Preparación (1-2 días)
1. ✅ Crear branch de feature: `feature/gcb-drift-adaptation`
2. ✅ Agregar secretos de AWS Access Keys en GitHub
3. ✅ Documentar diferencias (este documento)

### Fase 2: Implementación (3-5 días)
1. 🔲 Crear workflow híbrido o separado según preferencia
2. 🔲 Adaptar scripts de discovery
3. 🔲 Probar con cuenta de desarrollo de Gobierno de Córdoba
4. 🔲 Validar creación de issues y notificaciones

### Fase 3: Testing (2-3 días)
1. 🔲 Ejecutar drift detection manual en ambos modos
2. 🔲 Verificar que los issues se crean correctamente
3. 🔲 Validar notificaciones de Teams
4. 🔲 Confirmar que no hay duplicación de issues

### Fase 4: Rollout (1 día)
1. 🔲 Merge a main
2. 🔲 Activar schedule para ejecución diaria
3. 🔲 Monitorear primeras ejecuciones
4. 🔲 Documentar en README

---

## 📊 Comparación de Opciones

| Criterio | Opción A (Híbrida) | Opción B (Separada) | Opción C (shared-workflows) |
|----------|-------------------|---------------------|----------------------------|
| **Complejidad** | Media | Baja | Baja |
| **Mantenimiento** | Un solo workflow | Dos workflows | Centralizado |
| **Flexibilidad** | Alta | Media | Baja |
| **Reutilización** | Alta | Media | Muy Alta |
| **Control** | Total | Total | Limitado |
| **Tiempo implementación** | 5-7 días | 3-5 días | 1-2 días |

---

## 🎓 Recomendación Final

**Para tu caso específico, recomiendo la Opción A (Híbrida)** porque:

1. ✅ **Compatibilidad**: Funciona con ambos patrones sin cambios en proyectos existentes
2. ✅ **Flexibilidad**: Puedes elegir el modo de autenticación por proyecto
3. ✅ **Escalabilidad**: Fácil de extender a futuros patrones
4. ✅ **DRY**: No duplicas código, mantienes un solo workflow
5. ✅ **Auto-detección**: Identifica automáticamente el patrón correcto

**Próximo paso sugerido:**
Implementar primero la Opción B (más simple) como POC con una cuenta de Gobierno de Córdoba, y luego evolucionar a la Opción A una vez validado el funcionamiento.

---

## 📚 Referencias

- Workflow actual: `.github/workflows/terraform-drift-detection.yml`
- Shared workflows GCB: `/home/u633797/Descargas/shared-workflows/.github/workflows/`
- Proyecto CórdobaEmprendedora: `/home/u633797/Descargas/cordobaemprendedora/`
- Documentación drift detection: `docs/TERRAFORM_DRIFT_DETECTION_GUIDE.md`
