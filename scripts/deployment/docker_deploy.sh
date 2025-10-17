#!/bin/bash
# Docker Deployment Script for NBA Scrapers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="nba-scrapers"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_warning "AWS credentials not configured. Some features may not work."
    fi

    log_success "Prerequisites check completed"
}

# Create environment file
create_env_file() {
    log_info "Creating environment file..."

    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# NBA Scraper Environment Configuration

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=nba-sim-raw-data-lake

# Logging
LOG_LEVEL=INFO

# Scraper Modes
SCRAPER_MODE=incremental

# Monitoring
MONITORING_INTERVAL=60
DASHBOARD_PORT=8080

# Alerting
SLACK_WEBHOOK_URL=
SES_REGION=us-east-1
FROM_EMAIL=alerts@nba-simulator.com
TO_EMAILS=admin@nba-simulator.com

# Database (if using RDS)
DB_HOST=
DB_PORT=5432
DB_NAME=nba_data
DB_USER=
DB_PASSWORD=
EOF
        log_success "Environment file created: $ENV_FILE"
    else
        log_info "Environment file already exists: $ENV_FILE"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    docker-compose -f "$COMPOSE_FILE" build --no-cache

    log_success "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting NBA scraper services..."

    # Start core services first
    docker-compose -f "$COMPOSE_FILE" up -d health-monitor alert-manager

    # Wait for health monitor to be ready
    log_info "Waiting for health monitor to be ready..."
    sleep 10

    # Start scrapers
    docker-compose -f "$COMPOSE_FILE" up -d espn-scraper basketball-reference-scraper nba-api-scraper

    log_success "Services started successfully"
}

# Stop services
stop_services() {
    log_info "Stopping NBA scraper services..."

    docker-compose -f "$COMPOSE_FILE" down

    log_success "Services stopped successfully"
}

# Show status
show_status() {
    log_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    log_info "Health Dashboard: http://localhost:8080"
    log_info "Logs: docker-compose logs -f [service-name]"
}

# Show logs
show_logs() {
    local service=${1:-""}

    if [ -z "$service" ]; then
        log_info "Available services:"
        docker-compose -f "$COMPOSE_FILE" config --services
        echo ""
        log_info "Usage: $0 logs [service-name]"
        return
    fi

    log_info "Showing logs for $service..."
    docker-compose -f "$COMPOSE_FILE" logs -f "$service"
}

# Restart service
restart_service() {
    local service=$1

    if [ -z "$service" ]; then
        log_error "Service name required"
        echo "Usage: $0 restart [service-name]"
        return
    fi

    log_info "Restarting $service..."
    docker-compose -f "$COMPOSE_FILE" restart "$service"

    log_success "$service restarted successfully"
}

# Update service
update_service() {
    local service=$1

    if [ -z "$service" ]; then
        log_error "Service name required"
        echo "Usage: $0 update [service-name]"
        return
    fi

    log_info "Updating $service..."
    docker-compose -f "$COMPOSE_FILE" build "$service"
    docker-compose -f "$COMPOSE_FILE" up -d "$service"

    log_success "$service updated successfully"
}

# Clean up
cleanup() {
    log_info "Cleaning up Docker resources..."

    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" down -v

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    log_success "Cleanup completed"
}

# Health check
health_check() {
    log_info "Performing health check..."

    # Check if health monitor is responding
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Health monitor is responding"
    else
        log_error "Health monitor is not responding"
        return 1
    fi

    # Check container status
    local unhealthy_containers=$(docker-compose -f "$COMPOSE_FILE" ps --filter "health=unhealthy" -q)
    if [ -n "$unhealthy_containers" ]; then
        log_warning "Some containers are unhealthy:"
        docker-compose -f "$COMPOSE_FILE" ps --filter "health=unhealthy"
        return 1
    fi

    log_success "All services are healthy"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."

    local validation_passed=true

    # Check all containers are running
    log_info "Checking container status..."
    local running_containers=$(docker-compose ps --services --filter "status=running" | wc -l)
    local total_containers=$(docker-compose ps --services | wc -l)

    if [ "$running_containers" -eq "$total_containers" ]; then
        log_success "All containers are running ($running_containers/$total_containers)"
    else
        log_error "Not all containers are running ($running_containers/$total_containers)"
        validation_passed=false
    fi

    # Check health endpoints
    log_info "Checking health endpoints..."
    local health_url="http://localhost:8080/health"
    local health_response=$(curl -s -w "%{http_code}" -o /dev/null "$health_url" 2>/dev/null)

    if [ "$health_response" = "200" ]; then
        log_success "Health dashboard is accessible"
    else
        log_error "Health dashboard is not accessible (HTTP $health_response)"
        validation_passed=false
    fi

    # Check for error logs in last 5 minutes
    log_info "Checking for recent errors..."
    local error_count=$(docker-compose logs --since=5m 2>/dev/null | grep -i "error\|critical\|fatal" | wc -l)

    if [ "$error_count" -eq 0 ]; then
        log_success "No errors in last 5 minutes"
    else
        log_warning "Found $error_count errors in last 5 minutes"
        if [ "$error_count" -gt 10 ]; then
            log_error "Too many errors detected"
            validation_passed=false
        fi
    fi

    # Test S3 connectivity
    log_info "Testing S3 connectivity..."
    if aws s3 ls s3://nba-sim-raw-data-lake/ >/dev/null 2>&1; then
        log_success "S3 connectivity working"
    else
        log_error "S3 connectivity failed"
        validation_passed=false
    fi

    # Test alert system
    log_info "Testing alert system..."
    if python3 -c "
from scripts.monitoring.alert_manager import AlertManager
try:
    AlertManager().send_test_alert('Deployment validation test')
    print('Alert system functional')
except Exception as e:
    print(f'Alert system error: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "Alert system functional"
    else
        log_warning "Alert system test failed (non-critical)"
    fi

    # Final validation result
    if [ "$validation_passed" = true ]; then
        log_success "✅ Deployment validation PASSED"
        log_info "All services are healthy and operational"
        return 0
    else
        log_error "❌ Deployment validation FAILED"
        log_info "Please check the issues above before proceeding"
        return 1
    fi
}

# Backup data
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"

    log_info "Creating backup in $backup_dir..."

    mkdir -p "$backup_dir"

    # Backup logs
    if [ -d "logs" ]; then
        cp -r logs "$backup_dir/"
    fi

    # Backup data
    if [ -d "data" ]; then
        cp -r data "$backup_dir/"
    fi

    # Backup config
    if [ -d "config" ]; then
        cp -r config "$backup_dir/"
    fi

    log_success "Backup created: $backup_dir"
}

# Main menu
show_menu() {
    echo ""
    echo "NBA Scraper Docker Management"
    echo "============================="
    echo "1. Start all services"
    echo "2. Stop all services"
    echo "3. Show status"
    echo "4. Show logs"
    echo "5. Restart service"
    echo "6. Update service"
    echo "7. Health check"
    echo "8. Validate deployment"
    echo "9. Backup data"
    echo "10. Cleanup"
    echo "0. Exit"
    echo ""
    read -p "Select option: " choice

    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) show_status ;;
        4)
            echo "Available services:"
            docker-compose -f "$COMPOSE_FILE" config --services
            read -p "Enter service name: " service
            show_logs "$service"
            ;;
        5)
            echo "Available services:"
            docker-compose -f "$COMPOSE_FILE" config --services
            read -p "Enter service name: " service
            restart_service "$service"
            ;;
        6)
            echo "Available services:"
            docker-compose -f "$COMPOSE_FILE" config --services
            read -p "Enter service name: " service
            update_service "$service"
            ;;
        7) health_check ;;
        8) validate_deployment ;;
        9) backup_data ;;
        10) cleanup ;;
        0) exit 0 ;;
        *) log_error "Invalid option" ;;
    esac
}

# Main script logic
main() {
    case "${1:-menu}" in
        "start")
            check_prerequisites
            create_env_file
            build_images
            start_services
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "restart")
            restart_service "$2"
            ;;
        "update")
            update_service "$2"
            ;;
        "health")
            health_check
            ;;
        "validate")
            validate_deployment
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        "menu"|"")
            check_prerequisites
            create_env_file
            show_menu
            ;;
        *)
            echo "Usage: $0 [start|stop|status|logs|restart|update|health|validate|backup|cleanup|menu]"
            echo ""
            echo "Commands:"
            echo "  start     - Start all services"
            echo "  stop      - Stop all services"
            echo "  status    - Show service status"
            echo "  logs      - Show logs for a service"
            echo "  restart   - Restart a specific service"
            echo "  update    - Update a specific service"
            echo "  health    - Perform health check"
            echo "  validate  - Validate deployment"
            echo "  backup    - Backup data"
            echo "  cleanup   - Clean up Docker resources"
            echo "  menu      - Show interactive menu"
            ;;
    esac
}

# Run main function
main "$@"
