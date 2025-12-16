# Guía de Migración: Workflow Drift Detection GCB

## Resumen de Cambios

Se ha reemplazado el workflow de drift detection original con uno nuevo adaptado al patrón de Gobierno de Córdoba (GCB).

### Lo Que Cambió

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Archivo** | `terraform-drift-detection.yml` | `terraform-drift-detection-gcb.yml` |
| **Autenticación** | OIDC (OpenID Connect) | AWS Access Keys |
| **Discovery** | Terraform workspaces | Escaneo de directorios |
| **Estructura** | `environments/{env}` + workspaces | `environments/{cuenta}` directorios |
| **Backend** | Backend-config en runtime | Init directo en cada directorio |

### Lo Que NO Cambió

- Detección de drift con `terraform plan -detailed-exitcode`
- Creación de issues en GitHub con hash único
- Prevención de duplicados
- Notificaciones a Microsoft Teams
- Ejecución programada diaria a las 6 AM UTC
- Soporte para ejecución manual

---

## Pasos de Migración

### 1. Actualizar Secretos en GitHub

Necesitas cambiar los secretos de autenticación AWS:

**Secretos a ELIMINAR:**
- `AWS_ROLE_ARN` (ya no se usa OIDC)
- `TF_STATE_BUCKET` (opcional, dependiendo de tu configuración)
- `TF_STATE_KEY` (opcional, dependiendo de tu configuración)

**Secretos a AGREGAR:**

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Secretos que se mantienen:**
- `GH_TOKEN` - Para crear issues
- `TEAMS_WEBHOOK_URL` - (Opcional) Para notificaciones
- `AWS_REGION` - (Opcional) Si quieres sobreescribir us-east-2

#### Cómo agregar secretos en GitHub:

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Agrega cada secreto:
   - Name: `AWS_ACCESS_KEY_ID`
   - Secret: Tu access key
5. Repite para `AWS_SECRET_ACCESS_KEY`

### 2. Configurar el Provider de Terraform

Si necesitas asumir un rol específico, configúralo en el `provider.tf` de cada environment:

```hcl
# environments/010836206672/provider.tf
provider "aws" {
  region = "us-east-2"

  # Opcional: Si necesitas asumir un rol específico
  assume_role {
    role_arn = "arn:aws:iam::243425059285:role/terraform/deploy-role"
  }
}
```

### 3. Reorganizar Estructura de Environments (Si es necesario)

Si actualmente usas workspaces, necesitas reorganizar a directorios:

**Estructura anterior (workspaces):**
```
environments/
  └── dev/
      ├── main.tf
      ├── backend.tf
      └── ...
# Workspaces: dev, staging, prod
```

**Estructura nueva (directorios):**
```
environments/
  ├── 010836206672/    # Cuenta dev
  │   ├── main.tf
  │   ├── provider.tf
  │   └── ...
  ├── 020836206673/    # Cuenta staging
  │   ├── main.tf
  │   ├── provider.tf
  │   └── ...
  └── 030836206674/    # Cuenta prod
      ├── main.tf
      ├── provider.tf
      └── ...
```

#### Script de migración de workspaces a directorios:

```bash
#!/bin/bash
# migrate-to-directories.sh

# Crear nuevos directorios para cada cuenta
mkdir -p environments/010836206672  # dev
mkdir -p environments/020836206673  # staging
mkdir -p environments/030836206674  # prod

# Copiar configuración base
cp environments/dev/*.tf environments/010836206672/
cp environments/dev/*.tf environments/020836206673/
cp environments/dev/*.tf environments/030836206674/

# Actualizar variables en cada environment
# (Editar manualmente según tus necesidades)
```

### 4. Configurar Backend por Environment

Cada environment debe tener su propio backend configurado:

```hcl
# environments/010836206672/backend.tf
terraform {
  backend "s3" {
    bucket         = "terraform-state-010836206672"
    key            = "terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 5. Migrar Estado de Terraform (Si usabas workspaces)

Si estabas usando workspaces, necesitas migrar el estado:

```bash
# Para cada ambiente
cd environments/dev

# 1. Seleccionar workspace
terraform workspace select dev

# 2. Hacer backup del estado
terraform state pull > /tmp/state-dev.json

# 3. Copiar archivos al nuevo directorio
cd ../..
cp environments/dev/*.tf environments/010836206672/

# 4. Inicializar nuevo backend
cd environments/010836206672
terraform init

# 5. Importar estado (si es necesario)
# terraform state push /tmp/state-dev.json

# 6. Verificar
terraform plan
```

**IMPORTANTE:** Haz un backup completo del estado antes de migrar.

### 6. Actualizar GitHub Actions Environment

El workflow usa el environment `production` para aprobaciones:

1. Ve a Settings → Environments en GitHub
2. Crea/configura el environment `production`
3. Agrega reglas de protección si es necesario:
   - Required reviewers
   - Wait timer
   - Deployment branches

### 7. Probar el Workflow

#### Prueba manual:

1. Ve a Actions → Terraform Drift Detection (GCB)
2. Click en "Run workflow"
3. Especifica un target de prueba (ej: `010836206672`)
4. Click en "Run workflow"
5. Observa los logs

#### Verificar que funciona:

- ✅ Discovery detecta todos los environments
- ✅ Terraform init funciona en cada environment
- ✅ Terraform plan se ejecuta correctamente
- ✅ Si hay drift, se crea un issue en GitHub
- ✅ (Opcional) Notificación llega a Teams

---

## Troubleshooting

### Error: "Directory does not exist"

**Problema:** El workflow no encuentra el directorio del environment.

**Solución:**
```bash
# Verifica la estructura
ls -la environments/

# Debe mostrar directorios, no archivos
```

### Error: "No .tf files found"

**Problema:** El directorio existe pero no tiene archivos Terraform.

**Solución:**
```bash
# Verifica que hay archivos .tf
ls environments/010836206672/*.tf

# Si no hay, cópialos:
cp environments/dev/*.tf environments/010836206672/
```

### Error: "Terraform init failed"

**Problema:** El backend no está configurado correctamente.

**Solución:**
1. Verifica que el bucket S3 exista
2. Verifica que las credenciales tengan acceso
3. Verifica la configuración del backend.tf

```bash
cd environments/010836206672
terraform init -upgrade
```

### Error: "Access Denied" en AWS

**Problema:** Las credenciales no tienen permisos suficientes.

**Solución:**
1. Verifica que `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` sean correctos
2. Verifica que el usuario/rol tenga permisos para:
   - S3 (para el estado)
   - DynamoDB (para los locks)
   - Servicios que gestiona Terraform (EC2, VPC, etc.)

### No se crean issues

**Problema:** El drift se detecta pero no se crea issue.

**Solución:**
1. Verifica que `GH_TOKEN` esté configurado
2. Verifica que el token tenga scope `repo` (issues: write)
3. Verifica que los labels existan: `terraform`, `drift-detection`, `infrastructure`
   - O comenta la línea que agrega labels en el workflow

---

## Comparación de Configuración

### Configuración Anterior (OIDC)

```yaml
# .github/workflows/terraform-drift-detection.yml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ env.AWS_REGION }}

# Ejecución con workspaces
terraform workspace select dev
terraform plan
```

### Configuración Nueva (Access Keys)

```yaml
# .github/workflows/terraform-drift-detection-gcb.yml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-2

# Ejecución con directorios
cd environments/010836206672
terraform init
terraform plan
```

---

## Checklist de Migración

Usa este checklist para asegurarte de que completaste todos los pasos:

- [ ] Secretos AWS actualizados (Access Keys agregados)
- [ ] Estructura de environments reorganizada (si era necesario)
- [ ] Backend configurado en cada environment
- [ ] Estado de Terraform migrado (si usabas workspaces)
- [ ] Provider configurado con assume_role (si es necesario)
- [ ] GitHub Environment `production` configurado
- [ ] Workflow probado manualmente con éxito
- [ ] Discovery detecta todos los environments automáticamente
- [ ] Issues se crean correctamente cuando hay drift
- [ ] Notificaciones a Teams funcionan (si está configurado)
- [ ] Documentación actualizada (README, guías)

---

## Ventajas del Nuevo Workflow

1. **Discovery Automático**: Agrega o quita environments sin modificar código
2. **Más Simple**: No necesita workspaces de Terraform
3. **Multi-Cuenta**: Soporta múltiples cuentas AWS fácilmente
4. **Estándar GCB**: Compatible con el patrón de Gobierno de Córdoba
5. **Flexible**: Soporta configuraciones por cuenta/ambiente
6. **Paralelo**: Ejecuta drift detection en todos los environments simultáneamente

---

## Soporte

Si tienes problemas con la migración:

1. Revisa los logs del workflow en GitHub Actions
2. Consulta la documentación:
   - `docs/TERRAFORM_DRIFT_DETECTION_GUIDE.md`
   - `docs/ADAPTACION_GOBIERNO_CORDOBA.md`
3. Verifica la configuración de secretos en GitHub
4. Prueba terraform init y plan manualmente en cada environment

---

## Próximos Pasos

Una vez completada la migración:

1. Monitorea las primeras ejecuciones del workflow
2. Ajusta el schedule si es necesario (actualmente 6 AM UTC)
3. Configura las notificaciones de Teams si aún no lo hiciste
4. Documenta cualquier configuración específica de tus environments
5. Entrena a tu equipo en el nuevo workflow
