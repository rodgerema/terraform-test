# Terraform AWS Pipeline Project

Este proyecto implementa un pipeline completo de CI/CD para desplegar infraestructura en AWS usando Terraform y GitHub Actions.

## Estructura del Proyecto

```
terraform-test/
├── .github/workflows/          # GitHub Actions workflows
│   ├── terraform-plan.yml     # Validación en PRs
│   ├── terraform-apply.yml    # Deploy automático
│   └── terraform-destroy.yml  # Destroy de emergencia
├── environments/               # Configuraciones por ambiente
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/                    # Módulos Terraform reutilizables
│   ├── vpc/
│   ├── ec2/
│   └── rds/
└── scripts/                    # Scripts de utilidad
    ├── validate.sh
    └── format-check.sh
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

## Ambientes

- **dev**: Desarrollo (t3.micro)
- **staging**: Pre-producción (t3.small) 
- **prod**: Producción (t3.large)