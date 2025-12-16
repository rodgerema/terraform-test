# Terraform AWS Pipeline Project

Este proyecto implementa un pipeline completo de CI/CD para desplegar infraestructura en AWS usando Terraform y GitHub Actions.

## Estructura del Proyecto

```
terraform-test/
├── .github/workflows/                # GitHub Actions workflows
│   ├── terraform-plan.yml           # Validación en PRs
│   ├── terraform-apply.yml          # Deploy automático
│   ├── terraform-destroy.yml        # Destroy de emergencia
│   └── terraform-drift-detection-gcb.yml  # Detección de drift (GCB)
├── environments/                     # Configuraciones por ambiente
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/                          # Módulos Terraform reutilizables
│   ├── vpc/
│   ├── ec2/
│   └── rds/
└── scripts/                          # Scripts de utilidad
    ├── validate.sh
    └── format-check.sh
```

## Configuración Inicial

1. **Configurar Secrets en GitHub:**
   - `AWS_ACCESS_KEY_ID`: AWS Access Key ID
   - `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key
   - `AWS_REGION`: Región AWS (ej: us-east-2)
   - `GH_TOKEN`: GitHub Personal Access Token (para crear issues)
   - `TEAMS_WEBHOOK_URL`: (Opcional) Webhook de Microsoft Teams para notificaciones

2. **Configurar Backend S3:**
   - Crear bucket S3 para el state
   - Crear tabla DynamoDB para locks
   - Configurar rol IAM con permisos necesarios

## Uso

### Validación Local
```bash
./scripts/validate.sh dev
./scripts/format-check.sh
```

### Deploy Manual
```bash
cd environments/dev
terraform init
terraform plan
terraform apply
```

## Workflows

- **terraform-plan.yml**: Se ejecuta en PRs, valida y muestra el plan
- **terraform-apply.yml**: Deploy automático al merge en main
- **terraform-destroy.yml**: Destroy manual con confirmación
- **terraform-drift-detection-gcb.yml**: Detección automática de drift en infraestructura
  - Se ejecuta diariamente a las 6 AM UTC
  - Escanea automáticamente todos los environments en `environments/`
  - Crea issues en GitHub cuando detecta cambios
  - Envía notificaciones a Teams (si está configurado)
  - Soporta ejecución manual para environments específicos

## Ambientes

- **dev**: Desarrollo (t3.micro)
- **staging**: Pre-producción (t3.small)
- **prod**: Producción (t3.large)

## Detección de Drift

El workflow de drift detection monitorea automáticamente la infraestructura para detectar cambios no autorizados o divergencias entre el estado de Terraform y la infraestructura real en AWS.

### Características

- **Discovery Automático**: Escanea automáticamente todos los directorios en `environments/`
- **Ejecución Programada**: Corre diariamente a las 6 AM UTC
- **Detección de Duplicados**: Usa hashes para evitar crear issues duplicados
- **Notificaciones**: Crea issues en GitHub y envía alertas a Teams
- **Flexible**: Soporta ejecución manual para environments específicos

### Uso Manual

Para ejecutar el drift detection manualmente en un environment específico:

1. Ve a **Actions** en GitHub
2. Selecciona **Terraform Drift Detection (GCB)**
3. Click en **Run workflow**
4. Opcionalmente especifica:
   - **target**: Número de cuenta/environment específico (vacío para todos)
   - **aws_region**: Región AWS (por defecto: us-east-2)

### Cómo Funciona

1. **Discovery**: Escanea todos los subdirectorios en `environments/`
2. **Validation**: Verifica que cada directorio tenga archivos `.tf`
3. **Plan**: Ejecuta `terraform plan -detailed-exitcode` en cada environment
4. **Detection**: Si detecta cambios (exit code 2):
   - Genera un hash único del plan
   - Verifica si ya existe un issue abierto con ese hash
   - Crea un nuevo issue con los cambios detectados
   - Envía notificación a Teams (si está configurado)
5. **Tracking**: Los issues se etiquetan con: `terraform`, `drift-detection`, `infrastructure`

### Agregar Nuevos Environments

El workflow detecta automáticamente nuevos environments. Solo necesitas:

1. Crear un nuevo directorio en `environments/` (ej: `environments/123456789012`)
2. Agregar tus archivos de configuración Terraform (`.tf`)
3. Configurar el backend de Terraform si es necesario
4. El próximo run del workflow lo detectará automáticamente

### Troubleshooting

Si el drift detection falla:

1. Verifica que el directorio tenga archivos `.tf`
2. Verifica que `terraform init` funcione correctamente
3. Verifica que las credenciales AWS tengan permisos suficientes
4. Revisa los logs del workflow en GitHub Actions

Para más detalles, consulta:
- `docs/TERRAFORM_DRIFT_DETECTION_GUIDE.md` - Guía completa
- `docs/ADAPTACION_GOBIERNO_CORDOBA.md` - Documentación de adaptación para GCB