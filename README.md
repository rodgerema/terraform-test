# Terraform AWS Pipeline Project

Este proyecto implementa un pipeline completo de CI/CD para desplegar infraestructura en AWS usando Terraform y GitHub Actions.

## Estructura del Proyecto

```
terraform-test/
├── .github/workflows/                        # GitHub Actions workflows
│   ├── terraform-plan.yml                   # Validación en PRs
│   ├── terraform-apply.yml                  # Deploy automático
│   ├── terraform-destroy.yml                # Destroy de emergencia
│   ├── terraform-drift-detection.yml        # Detección de drift
│   └── terraform-drift-detection-metrics.yml # Métricas de issues de drift
├── environments/                             # Configuraciones por ambiente
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/                                  # Módulos Terraform reutilizables
│   ├── vpc/
│   ├── ec2/
│   └── rds/
├── scripts/                                  # Scripts de utilidad
│   ├── github_drift_issues.py               # Script de métricas de drift
│   ├── requirements.txt                     # Dependencias Python
│   ├── validate.sh
│   └── format-check.sh
├── templates/                                # Templates HTML
│   └── drift_report.html                    # Template para reportes
└── docs/                                     # Documentación
    ├── TERRAFORM_DRIFT_DETECTION_GUIDE.md
    └── DRIFT_METRICS_IMPLEMENTATION.md      # Guía de implementación
```

## Configuración Inicial

1. **Configurar Secrets en GitHub:**
   - `AWS_ACCOUNT_ID`: ID de la cuenta AWS
   - `AWS_ROLE_ARN`: ARN del rol IAM para GitHub Actions
   - `AWS_REGION`: Región AWS (ej: us-east-1)
   - `TF_STATE_BUCKET`: Bucket S3 para el state
   - `TF_STATE_KEY`: Key del state file

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
- **terraform-drift-detection.yml**: Detecta drift en la infraestructura y crea issues
- **terraform-drift-detection-metrics.yml**: Genera reportes HTML con métricas de issues de drift

## Drift Detection Metrics

El workflow `terraform-drift-detection-metrics.yml` analiza los issues de drift creados en el repositorio y genera un reporte HTML con:

- Total de issues de drift en los últimos 30 días
- Detalle por repositorio
- Timeline de detecciones
- Exportación como artefacto descargable

### Ejecución

- **Automática**: Diariamente a las 8:00 AM UTC
- **Manual**: Actions → Terraform Drift Detection Metrics → Run workflow

### Documentación

- [Guía de Implementación](docs/DRIFT_METRICS_IMPLEMENTATION.md) - Cómo implementar en otro repositorio
- [Guía Completa de Drift Detection](docs/TERRAFORM_DRIFT_DETECTION_GUIDE.md)

## Ambientes

- **dev**: Desarrollo (t3.micro)
- **staging**: Pre-producción (t3.small) 
- **prod**: Producción (t3.large)