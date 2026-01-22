#!/usr/bin/env python3

import sys
import json
import requests
import re
from datetime import datetime
from urllib.parse import quote, urlparse
from colorama import init, Fore, Back, Style
import time
import os
from collections import defaultdict
# Importaciones para HTML
import html
from datetime import datetime, timedelta

# Initialize colorama for cross-platform colored output
init()

class TelecomConsole:
    """Terraform Drift Detection Metrics - TELECOM ARGENTINA"""
    
    # Esquema de colores corporativos TELECOM ARGENTINA
    COLORS = {
        'header': Fore.BLUE + Style.BRIGHT,      # Azul corporativo principal
        'success': Fore.GREEN + Style.BRIGHT,
        'error': Fore.RED + Style.BRIGHT,
        'warning': Fore.YELLOW + Style.BRIGHT,
        'info': Fore.CYAN + Style.BRIGHT,        # Azul claro para información
        'prompt': Fore.BLUE + Style.BRIGHT,      # Azul corporativo para prompts
        'data': Fore.WHITE + Style.BRIGHT,
        'border': Fore.BLUE + Style.DIM,         # Azul tenue para bordes
        'reset': Style.RESET_ALL
    }
    
    @staticmethod
    def print_banner():
        """Mostrar banner corporativo de TELECOM ARGENTINA"""
        banner = f"""
{TelecomConsole.COLORS['header']}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📡 TERRAFORM DRIFT DETECTION METRICS 📡                     ║
║                         TELECOM ARGENTINA - 2025                           ║
║                      Sistema de Monitoreo de Infraestructura               ║
╚══════════════════════════════════════════════════════════════════════════════╝
{TelecomConsole.COLORS['reset']}"""
        print(banner)
        time.sleep(0.5)
    
    @staticmethod
    def print_section(title):
        """Mostrar encabezado de sección con estilo corporativo"""
        print(f"\n{TelecomConsole.COLORS['border']}{'═' * 80}{TelecomConsole.COLORS['reset']}")
        print(f"{TelecomConsole.COLORS['header']}📋 {title}{TelecomConsole.COLORS['reset']}")
        print(f"{TelecomConsole.COLORS['border']}{'═' * 80}{TelecomConsole.COLORS['reset']}\n")
    
    @staticmethod
    def print_success(message):
        """Mostrar mensaje de éxito"""
        print(f"{TelecomConsole.COLORS['success']}✓ {message}{TelecomConsole.COLORS['reset']}")
    
    @staticmethod
    def print_error(message):
        """Mostrar mensaje de error"""
        print(f"{TelecomConsole.COLORS['error']}⚠️ ERROR: {message}{TelecomConsole.COLORS['reset']}")
    
    @staticmethod
    def print_warning(message):
        """Mostrar mensaje de advertencia"""
        print(f"{TelecomConsole.COLORS['warning']}⚠️ ADVERTENCIA: {message}{TelecomConsole.COLORS['reset']}")
    
    @staticmethod
    def print_info(message):
        """Mostrar mensaje informativo"""
        print(f"{TelecomConsole.COLORS['info']}📝 {message}{TelecomConsole.COLORS['reset']}")
    
    
    @staticmethod
    def loading_animation(message):
        """Mostrar animación de carga"""
        print(f"{TelecomConsole.COLORS['info']}⏳ {message}", end="")
        for _ in range(3):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print(f" ✅ COMPLETADO! {TelecomConsole.COLORS['reset']}")

class TelecomDriftDetector:
    """Clase principal para detección de drift - TELECOM ARGENTINA"""
    
    def __init__(self):
        self.api_key = None
        self.repo_path = None
        self.org_path = None
        self.is_org = False
        self.github_url = "https://api.github.com"
        self.start_date = None
        self.end_date = None
        self.console = TelecomConsole()
        self.all_issues = []  # Para almacenar todos los issues de todos los repositorios
        self.timeline_data = []  # Para almacenar datos temporales para el gráfico
        self._set_default_dates()  # Configurar fechas por defecto (últimos 30 días)
    
    def show_help(self):
        """Mostrar información de ayuda"""
        self.console.print_section("AYUDA - DETECTOR DE DRIFT TELECOM ARGENTINA")
        help_text = """
📋 OBJETIVO: Consultar issues de GitHub con título 'Drift detected'

🔧 CARACTERÍSTICAS:
  • Configuración vía variables de entorno
  • Soporte para URLs de repositorios individuales u organizaciones completas
  • Escaneo de todos los repositorios dentro de una organización
  • Rango de fechas automático: últimos 30 días (configurable vía variables)
  • Reporte agrupado por repositorio con totales
  • Exportación a HTML con información detallada por repositorio
  • Interfaz corporativa TELECOM ARGENTINA
  
📝 TIPOS DE URL SOPORTADAS:
  • Repositorio individual: https://github.com/owner/repo
  • Organización completa: https://github.com/org (escanea todos los repositorios)
  • Repositorios de usuario: https://github.com/username
  
📝 CONTROLES:
  • Configurar variables de entorno antes de ejecutar
  • Usar -h o --help para mostrar esta ayuda
  
⚙️ REQUISITOS:
  • Python 3.6+
  • librería requests
  • librería colorama
  • librería reportlab (para reportes PDF)
  • librería matplotlib (opcional, para gráficos)
  
🚀 USO: 
  export GH_TOKEN="your_token"
  export GH_URL="https://github.com/owner/repo"
  python3 github_drift_issues.py
  
  • Automáticamente analiza los últimos 30 días
  • Ideal para ejecución en pipelines programados
        """
        print(help_text)
    
    def validate_date(self, date_string):
        """Validar formato de fecha y retornar True si es válida"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            self.console.print_error(f"Fecha inválida '{date_string}'. Use formato YYYY-MM-DD")
            return False
    
    def extract_path_from_url(self, url):
        """Extraer ruta del repositorio u organización desde URL de GitHub"""
        # Remover protocolo
        url = re.sub(r'^https?://', '', url)
        
        # Extraer el dominio para determinar la instancia de GitHub
        url_parts = url.split('/')
        if len(url_parts) > 0:
            domain = url_parts[0]
            if domain != 'github.com':
                self.github_url = f"https://api.{domain}"
        
        # Remover dominio
        path = re.sub(r'^[^/]*/', '', url)
        
        # Remover sufijo .git si existe
        path = re.sub(r'\.git$', '', path)
        
        # Remover trailing slashes
        path = path.rstrip('/')
        
        if not path:
            self.console.print_error("URL inválida. Debe contener una ruta válida")
            return None, False
        
        # Determinar si es una organización o repositorio
        # Si contiene exactamente una barra, es un repositorio (owner/repo)
        # Si no contiene barra, es una organización
        slash_count = path.count('/')
        
        if slash_count == 0:
            # Solo el nombre de la organización
            return path, True
        elif slash_count == 1:
            # owner/repo - repositorio específico
            return path, False
        
        return path, False
    
    def _set_default_dates(self):
        """Configurar fechas por defecto: últimos 30 días"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        self.end_date = end_date.strftime('%Y-%m-%d')
        self.start_date = start_date.strftime('%Y-%m-%d')
    
    def get_env_config(self):
        """Obtener configuración desde variables de entorno"""
        self.api_key = os.getenv('GH_TOKEN')
        github_url = os.getenv('GH_URL')
        
        # Las fechas están configuradas por defecto en __init__ para los últimos 30 días
        # No se permiten fechas personalizadas
        
        # Validar variables requeridas
        missing_vars = []
        if not self.api_key:
            missing_vars.append('GH_TOKEN')
        if not github_url:
            missing_vars.append('GH_URL')
        
        if missing_vars:
            self.console.print_error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
            return False
        
        # Procesar URL
        path, is_org = self.extract_path_from_url(github_url)
        if not path:
            return False
        
        if is_org:
            self.org_path = path
            self.is_org = True
        else:
            self.repo_path = path
            self.is_org = False
        
        return True

    
    def get_org_repos(self, org_path):
        """Obtener todos los repositorios de una organización"""
        headers = {
            'Authorization': f'token {self.api_key}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Obtener repositorios de la organización
        api_url = f"{self.github_url}/orgs/{org_path}/repos"
        params = {
            'per_page': 100,
            'type': 'all'
        }
        
        all_repos = []
        page = 1
        
        while True:
            params['page'] = page
            try:
                response = requests.get(api_url, headers=headers, params=params)
                response.raise_for_status()
                repos = response.json()
                
                if isinstance(repos, dict) and 'message' in repos:
                    self.console.print_error(f"Error de API GitHub: {repos['message']}")
                    return []
                
                if not repos:
                    break
                    
                all_repos.extend(repos)
                page += 1
                
                # Si hay menos de 100 repositorios, es la última página
                if len(repos) < 100:
                    break
                    
            except requests.exceptions.RequestException as e:
                self.console.print_error(f"Error al obtener repositorios de la organización: {str(e)}")
                return []
        
        return all_repos
    
    def query_repo_issues(self, repo_path):
        """Consultar issues de un repositorio específico"""
        headers = {
            'Authorization': f'token {self.api_key}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # GitHub usa q (query) para búsquedas complejas
        # Buscar "Drift detected" (inglés) que es el formato usado por terraform-drift-detection
        query = f'repo:{repo_path} "Drift detected" in:title state:open created:{self.start_date}..{self.end_date}'
        
        search_url = f"{self.github_url}/search/issues"
        params = {
            'q': query,
            'per_page': 100
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # GitHub search API devuelve un objeto con 'items'
            if 'items' not in result:
                return []
            
            issues = result['items']
            
            # Agregar información del repositorio a cada issue
            for issue in issues:
                issue['repo_path'] = repo_path
                issue['repo_name'] = repo_path.split('/')[-1]
                # Mapear campos de GitHub a formato similar a GitLab
                issue['iid'] = issue['number']
                issue['web_url'] = issue['html_url']
                issue['created_at'] = issue['created_at']
                issue['author'] = issue['user']
            
            return issues
            
        except requests.exceptions.RequestException:
            return []
        except json.JSONDecodeError:
            return []
    
    def query_github_issues(self):
        """Consultar API de GitHub para issues de detección de drift"""
        self.console.print_section("CONSULTANDO API DE GITHUB")
        
        if self.is_org:
            self.console.print_info(f"Organización: {self.org_path}")
            self.console.print_info("Obteniendo lista de repositorios...")
            
            # Mostrar animación de carga
            self.console.loading_animation("Conectando a API de GitHub")
            
            # Obtener todos los repositorios de la organización
            repos = self.get_org_repos(self.org_path)
            
            if not repos:
                self.console.print_warning("No se encontraron repositorios en la organización especificada.")
                return
            
            self.console.print_success(f"Se encontraron {len(repos)} repositorio(s) en la organización")
            print()
            
            # Consultar issues para cada repositorio
            repo_issues = defaultdict(list)
            total_issues = 0
            
            for i, repo in enumerate(repos, 1):
                repo_path = repo['full_name']
                self.console.print_info(f"[{i}/{len(repos)}] Escaneando: {repo_path}")
                
                issues = self.query_repo_issues(repo_path)
                if issues:
                    repo_issues[repo_path] = issues
                    total_issues += len(issues)
                    self.console.print_success(f"  → {len(issues)} issue(s) encontrado(s)")
            
            self.all_issues = repo_issues
            
        else:
            self.console.print_info(f"Repositorio: {self.repo_path}")
            self.console.loading_animation("Conectando a API de GitHub")
            
            issues = self.query_repo_issues(self.repo_path)
            if issues:
                self.all_issues = {self.repo_path: issues}
                total_issues = len(issues)
            else:
                self.all_issues = {}
                total_issues = 0
        
        self.console.print_info(f"Rango de fechas: {self.start_date} a {self.end_date}")
        print()
        
        if total_issues == 0:
            self.console.print_warning("No se encontraron issues abiertos con título 'Drift detected' en el rango de fechas especificado.")
            return
        
        # Mostrar y guardar resultados
        self.display_and_save_results()
        
        # Generar reporte HTML con tabla y gráfico
        self.generate_html_report()
    
    def display_and_save_results(self):
        """Mostrar resultados agrupados por repositorio"""
        total_issues = sum(len(issues) for issues in self.all_issues.values())
        
        self.console.print_section(f"RESULTADOS DETECCIÓN DE DRIFT - {total_issues} ISSUE(S) ENCONTRADO(S)")
        
        timeline_data = []
        
        # Mostrar issues agrupados por repositorio
        for repo_path, issues in sorted(self.all_issues.items()):
            if not issues:
                continue
                
            print(f"\n{TelecomConsole.COLORS['header']}📁 REPOSITORIO: {repo_path} ({len(issues)} issue(s)){TelecomConsole.COLORS['reset']}")
            print(f"{TelecomConsole.COLORS['border']}{'─' * 100}{TelecomConsole.COLORS['reset']}")
            
            # Encabezado de tabla
            print(f"{TelecomConsole.COLORS['data']}")
            print(f"{'ID':<8} {'TÍTULO':<50} {'ESTADO':<12} {'CREADO':<15} {'AUTOR':<20}")
            print("─" * 105)
            
            # Mostrar issues del repositorio
            for issue in issues:
                issue_id = str(issue['iid'])
                title_display = issue['title'][:47] + "..." if len(issue['title']) > 47 else issue['title']
                title_full = issue['title']
                state = issue['state']
                created = issue['created_at'].split('T')[0]
                created_full = issue['created_at']
                url = issue['web_url']
                author = issue.get('author', {}).get('login', 'N/A')[:17] + "..." if len(issue.get('author', {}).get('login', 'N/A')) > 17 else issue.get('author', {}).get('login', 'N/A')
                author_full = issue.get('author', {}).get('login', 'N/A')
                labels = ', '.join([label['name'] for label in issue.get('labels', [])])
                
                print(f"{issue_id:<8} {title_display:<50} {state:<12} {created:<15} {author:<20}")
                
                # Agregar datos para el timeline
                timeline_data.append({
                    'Repositorio': repo_path,
                    'ID': issue_id,
                    'Título': title_full,
                    'Estado': state,
                    'Fecha_Creación': created,
                    'Fecha_Creación_Completa': created_full,
                    'URL': url,
                    'Autor': author_full,
                    'Etiquetas': labels
                })
        
        print(f"{TelecomConsole.COLORS['reset']}")
        
        # Preparar datos para el timeline
        self.prepare_timeline_data(timeline_data)
        
        print(f"\n{TelecomConsole.COLORS['success']}📊 OPERACIÓN EXITOSA! Se encontraron {total_issues} issue(s) de detección de drift{TelecomConsole.COLORS['reset']}")
    
    
    def prepare_timeline_data(self, issues_data):
        """Preparar datos para el gráfico de timeline"""
        if not issues_data:
            return
        
        # Agrupar issues por fecha
        date_counts = defaultdict(int)
        for issue in issues_data:
            date = issue['Fecha_Creación']
            date_counts[date] += 1
        
        # Los datos ya están organizados por fecha
        
        # Crear lista completa de fechas (incluir fechas sin issues)
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        current_date = start_date
        self.timeline_data = []
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            count = date_counts.get(date_str, 0)
            self.timeline_data.append({
                'date': current_date,
                'date_str': date_str,
                'count': count
            })
            current_date += timedelta(days=1)
    
    def generate_html_report(self):
        """Generar reporte HTML con tabla de issues y gráfico de timeline"""
        if not self.all_issues:
            return
        
        # Nombre del archivo HTML
        if self.is_org:
            html_filename = f"drift_issues_report_org_{self.org_path.replace('/', '_')}_{self.start_date}_to_{self.end_date}.html"
        else:
            html_filename = f"drift_issues_report_{self.repo_path.replace('/', '_')}_{self.start_date}_to_{self.end_date}.html"
        
        try:
            self.console.print_info("Generando reporte HTML...")
            
            # Leer template HTML
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'drift_report.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Preparar datos para el template
            target = self.org_path if self.is_org else self.repo_path
            target_type = "Organización" if self.is_org else "Repositorio"
            total_issues = sum(len(issues) for issues in self.all_issues.values())
            total_repos = len([r for r, issues in self.all_issues.items() if issues])
            
            # Calcular período en días
            start_date_obj = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(self.end_date, '%Y-%m-%d')
            period_days = (end_date_obj - start_date_obj).days + 1
            
            # Calcular promedio diario
            avg_issues_per_day = round(total_issues / period_days, 1) if period_days > 0 else 0
            
            # Preparar datos de repositorios para el template
            repos_data = []
            for repo_path, issues in sorted(self.all_issues.items()):
                if not issues:
                    continue
                    
                repo_issues = []
                for issue in issues:
                    repo_issues.append({
                        'id': issue['iid'],
                        'title': html.escape(issue['title']),
                        'state': issue['state'],
                        'created_date': issue['created_at'].split('T')[0],
                        'author': html.escape(issue.get('author', {}).get('login', 'N/A'))
                    })
                
                repos_data.append({
                    'repo_name': repo_path,
                    'issue_count': len(issues),
                    'issues': repo_issues
                })
            
            # Preparar datos del timeline para Chart.js
            timeline_labels = []
            timeline_data_points = []
            
            if self.timeline_data:
                for item in self.timeline_data:
                    timeline_labels.append(item['date_str'])
                    timeline_data_points.append(item['count'])
            
            timeline_chart_data = {
                'labels': timeline_labels,
                'data': timeline_data_points
            }
            
            # Preparar variables para el template
            template_vars = {
                'target': html.escape(target),
                'target_type': target_type,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'total_issues': total_issues,
                'total_repos': total_repos,
                'period_days': period_days,
                'avg_issues_per_day': avg_issues_per_day,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'has_issues': total_issues > 0,
                'repos': repos_data,
                'timeline_data_json': json.dumps(timeline_chart_data)
            }
            
            # Generar HTML para repositorios
            if template_vars['has_issues']:
                repos_html = ""
                for repo in repos_data:
                    issues_html = ""
                    for issue in repo['issues']:
                        issues_html += f"""
                            <tr>
                                <td class="issue-id">#{issue['id']}</td>
                                <td class="issue-title">{issue['title']}</td>
                                <td>
                                    <span class="issue-state state-{issue['state']}">{issue['state']}</span>
                                </td>
                                <td>{issue['created_date']}</td>
                                <td class="author-info">{issue['author']}</td>
                            </tr>"""
                    
                    repos_html += f"""
            <div class="repo-section">
                <div class="table-container">
                    <div class="repo-header">
                        📁 {html.escape(repo['repo_name'])}
                        <span class="repo-count">{repo['issue_count']} issue(s)</span>
                    </div>
                    <table class="issues-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Título</th>
                                <th>Estado</th>
                                <th>Fecha Creación</th>
                                <th>Autor</th>
                            </tr>
                        </thead>
                        <tbody>{issues_html}
                        </tbody>
                    </table>
                </div>
            </div>"""
            else:
                repos_html = """
            <div class="no-issues">
                <div class="no-issues-icon">📋</div>
                <h3>No se encontraron issues de drift</h3>
                <p>No hay issues abiertos con título 'Drift detected' en el período especificado.</p>
            </div>"""
            
            # Agregar repos_html a las variables del template
            template_vars['repos_html'] = repos_html
            
            # Reemplazar variables en el template
            html_content = template_content
            for key, value in template_vars.items():
                if key == 'timeline_data_json':
                    # Usar triple llaves para timeline_data_json (debe ser JSON sin escapar)
                    html_content = html_content.replace('{{{' + key + '}}}', str(value))
                else:
                    html_content = html_content.replace('{{' + key + '}}', str(value))
            
            # Escribir archivo HTML
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.console.print_success(f"Reporte HTML generado: {html_filename}")
            
        except Exception as e:
            self.console.print_error(f"Error al generar reporte HTML: {str(e)}")
            self.console.print_warning("Asegúrese de que el template HTML esté disponible en: templates/drift_report.html")
    
    # Ya no necesitamos crear gráficos con matplotlib
    # El gráfico se genera en el navegador con Chart.js

def main():
    """Función principal"""
    detector = TelecomDriftDetector()
    
    # Verificar argumento de ayuda
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        detector.show_help()
        return
    
    # Verificar dependencias
    try:
        import requests
        import colorama
    except ImportError as e:
        print(f"Error: Falta librería requerida: {e}")
        print("Instalar con: pip install requests colorama")
        sys.exit(1)
    
    # Mostrar banner
    detector.console.print_banner()
    
    try:
        # Obtener configuración desde variables de entorno (OBLIGATORIO)
        if not detector.get_env_config():
            # Si no se pueden obtener las variables de entorno, terminar el programa
            detector.console.print_error("El script requiere las siguientes variables de entorno:")
            detector.console.print_error("  GH_TOKEN: Token de acceso a GitHub")
            detector.console.print_error("  GH_URL: URL del repositorio u organización de GitHub")
            detector.console.print_error("")
            detector.console.print_info("El script analiza automáticamente los últimos 30 días")
            sys.exit(1)
        
        # Configuración exitosa desde variables de entorno
        detector.console.print_section("CONFIGURACIÓN DESDE VARIABLES DE ENTORNO")
        target = detector.org_path if detector.is_org else detector.repo_path
        target_type = "Organización" if detector.is_org else "Repositorio"
        detector.console.print_success(f"{target_type}: {target}")
        detector.console.print_success(f"Período (últimos 30 días): {detector.start_date} a {detector.end_date}")
        
        detector.query_github_issues()
        
        # Mensaje de finalización
        print(f"\n{TelecomConsole.COLORS['header']}📊 SISTEMA FINALIZADO - ¡Gracias por usar TELECOM ARGENTINA! 📊{TelecomConsole.COLORS['reset']}")
        
    except KeyboardInterrupt:
        print(f"\n{TelecomConsole.COLORS['warning']}⏸️  Sistema interrumpido por el usuario. ¡Hasta luego!{TelecomConsole.COLORS['reset']}")
    except Exception as e:
        print(f"\n{TelecomConsole.COLORS['error']}⚠️ ERROR CRÍTICO: {str(e)}{TelecomConsole.COLORS['reset']}")

if __name__ == "__main__":
    main()