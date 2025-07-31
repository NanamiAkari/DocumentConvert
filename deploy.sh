#!/bin/bash

# 文档转换调度系统部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|status|logs|build]

set -e

# 配置变量
DEFAULT_COMPOSE_FILE="docker-compose.document-scheduler.yml"
GPU_COMPOSE_FILE="docker-compose.gpu.yml"
CPU_COMPOSE_FILE="docker-compose.cpu.yml"
SERVICE_NAME="document-scheduler"
IMAGE_NAME="document-scheduler"
VERSION="v1.0.0"

# 默认使用CPU版本
COMPOSE_FILE="$CPU_COMPOSE_FILE"
BUILD_TARGET="cpu"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose（支持新旧版本）
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_info "使用Docker Compose: $DOCKER_COMPOSE"
}

# 检测GPU支持
check_gpu_support() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            log_info "检测到NVIDIA GPU支持"
            return 0
        else
            log_warning "nvidia-smi命令存在但无法访问GPU"
            return 1
        fi
    else
        log_info "未检测到NVIDIA GPU支持"
        return 1
    fi
}

# 选择部署版本
select_version() {
    local version_type="$1"

    case "$version_type" in
        gpu)
            if check_gpu_support; then
                COMPOSE_FILE="$GPU_COMPOSE_FILE"
                BUILD_TARGET="gpu"
                log_info "选择GPU版本部署"
            else
                log_error "系统不支持GPU，无法使用GPU版本"
                exit 1
            fi
            ;;
        cpu)
            COMPOSE_FILE="$CPU_COMPOSE_FILE"
            BUILD_TARGET="cpu"
            log_info "选择CPU版本部署"
            ;;
        auto)
            if check_gpu_support; then
                COMPOSE_FILE="$GPU_COMPOSE_FILE"
                BUILD_TARGET="gpu"
                log_info "自动选择GPU版本部署"
            else
                COMPOSE_FILE="$CPU_COMPOSE_FILE"
                BUILD_TARGET="cpu"
                log_info "自动选择CPU版本部署"
            fi
            ;;
        *)
            log_error "未知版本类型: $version_type"
            log_info "支持的版本: gpu, cpu, auto"
            exit 1
            ;;
    esac
}

# 检查必要的目录
check_directories() {
    log_info "检查必要的目录..."
    
    # 创建输出目录
    if [ ! -d "./output" ]; then
        mkdir -p ./output
        log_info "创建输出目录: ./output"
    fi
    
    # 创建日志目录
    if [ ! -d "./logs" ]; then
        mkdir -p ./logs
        log_info "创建日志目录: ./logs"
    fi
    
    # 创建临时目录
    if [ ! -d "./temp" ]; then
        mkdir -p ./temp
        log_info "创建临时目录: ./temp"
    fi
    
    # 设置权限
    chmod 755 ./output ./logs ./temp
    log_success "目录检查完成"
}

# 构建镜像
build_image() {
    local target_version="${1:-$BUILD_TARGET}"
    log_info "开始构建Docker镜像 ($target_version 版本)..."

    local dockerfile=""
    case "$target_version" in
        gpu)
            dockerfile="Dockerfile.gpu"
            ;;
        cpu)
            dockerfile="Dockerfile.cpu"
            ;;
        *)
            dockerfile="Dockerfile.document-scheduler"
            ;;
    esac

    if [ ! -f "$dockerfile" ]; then
        log_error "Dockerfile文件不存在: $dockerfile"
        exit 1
    fi

    docker build -f "$dockerfile" -t "${IMAGE_NAME}:${target_version}" .
    docker tag "${IMAGE_NAME}:${target_version}" "${IMAGE_NAME}:${target_version}-${VERSION}"

    if [ "$target_version" = "cpu" ]; then
        docker tag "${IMAGE_NAME}:${target_version}" "${IMAGE_NAME}:latest"
        docker tag "${IMAGE_NAME}:${target_version}" "${IMAGE_NAME}:stable"
    fi

    log_success "镜像构建完成"
    docker images | grep ${IMAGE_NAME}
}

# 启动服务
start_service() {
    log_info "启动文档转换调度系统..."
    
    check_directories
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    # 检查镜像是否存在
    if ! docker images | grep -q ${IMAGE_NAME}; then
        log_warning "镜像不存在，开始构建..."
        build_image
    fi
    
    $DOCKER_COMPOSE -f $COMPOSE_FILE up -d
    
    log_success "服务启动完成"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查健康状态
    check_health
}

# 停止服务
stop_service() {
    log_info "停止文档转换调度系统..."
    
    $DOCKER_COMPOSE -f $COMPOSE_FILE down
    
    log_success "服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启文档转换调度系统..."
    
    stop_service
    sleep 5
    start_service
}

# 查看服务状态
check_status() {
    log_info "检查服务状态..."
    
    echo "=== Docker容器状态 ==="
    $DOCKER_COMPOSE -f $COMPOSE_FILE ps
    
    echo -e "\n=== 端口监听状态 ==="
    if command -v netstat &> /dev/null; then
        netstat -tlnp | grep :8000 || echo "端口8000未监听"
    else
        ss -tlnp | grep :8000 || echo "端口8000未监听"
    fi
    
    echo -e "\n=== 镜像信息 ==="
    docker images | grep ${IMAGE_NAME} || echo "未找到相关镜像"
}

# 检查健康状态
check_health() {
    log_info "检查API健康状态..."
    
    # 等待API启动
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API服务正常运行"
            curl -s http://localhost:8000/health | python3 -m json.tool
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    log_error "API服务启动失败或超时"
    return 1
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    
    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f --tail=50
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止并删除容器
    $DOCKER_COMPOSE -f $COMPOSE_FILE down --remove-orphans
    
    # 删除未使用的镜像（可选）
    read -p "是否删除未使用的Docker镜像? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        log_success "已清理未使用的镜像"
    fi
    
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    echo "文档转换调度系统部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令] [选项]"
    echo ""
    echo "可用命令:"
    echo "  start [gpu|cpu|auto]  启动服务"
    echo "  stop                  停止服务"
    echo "  restart [gpu|cpu|auto] 重启服务"
    echo "  status                查看服务状态"
    echo "  health                检查API健康状态"
    echo "  logs                  查看服务日志"
    echo "  build [gpu|cpu|both]  构建Docker镜像"
    echo "  cleanup               清理Docker资源"
    echo "  gpu-check             检查GPU支持"
    echo "  help                  显示此帮助信息"
    echo ""
    echo "版本选项:"
    echo "  gpu   使用GPU加速版本（需要NVIDIA GPU支持）"
    echo "  cpu   使用CPU优化版本（适用于所有环境）"
    echo "  auto  自动检测并选择最佳版本"
    echo "  both  构建GPU和CPU两个版本"
    echo ""
    echo "示例:"
    echo "  $0 start auto         # 自动选择版本启动服务"
    echo "  $0 start gpu          # 使用GPU版本启动"
    echo "  $0 start cpu          # 使用CPU版本启动"
    echo "  $0 build both         # 构建两个版本"
    echo "  $0 gpu-check          # 检查GPU支持"
    echo "  $0 logs               # 查看日志"
}

# 主函数
main() {
    # 检查Docker环境
    check_docker

    local command="${1:-help}"
    local version_option="${2:-auto}"

    case "$command" in
        start)
            select_version "$version_option"
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            select_version "$version_option"
            restart_service
            ;;
        status)
            check_status
            ;;
        health)
            check_health
            ;;
        logs)
            view_logs
            ;;
        build)
            if [ "$version_option" = "both" ]; then
                build_image "cpu"
                build_image "gpu"
            else
                select_version "$version_option"
                build_image "$BUILD_TARGET"
            fi
            ;;
        cleanup)
            cleanup
            ;;
        gpu-check)
            if check_gpu_support; then
                log_success "系统支持GPU加速"
                nvidia-smi
            else
                log_warning "系统不支持GPU加速"
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
