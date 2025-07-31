#!/bin/bash

# 文档转换调度系统镜像导出脚本
# 用于将Docker镜像导出为tar文件，便于离线部署

set -e

# 配置变量
IMAGE_NAME="document-scheduler"
VERSION="v1.0.0"
EXPORT_DIR="./docker-images"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
}

# 导出镜像
export_image() {
    log_info "开始导出Docker镜像..."
    
    # 创建导出目录
    mkdir -p "$EXPORT_DIR"
    
    # 检查镜像是否存在
    if ! docker images | grep -q "$IMAGE_NAME"; then
        log_error "镜像 $IMAGE_NAME 不存在，请先构建镜像"
        exit 1
    fi
    
    # 导出镜像
    local export_file="$EXPORT_DIR/${IMAGE_NAME}_${VERSION}_${TIMESTAMP}.tar"
    
    log_info "导出镜像到: $export_file"
    docker save -o "$export_file" \
        "${IMAGE_NAME}:latest" \
        "${IMAGE_NAME}:${VERSION}" \
        "${IMAGE_NAME}:stable"
    
    # 压缩镜像文件
    log_info "压缩镜像文件..."
    gzip "$export_file"
    
    local compressed_file="${export_file}.gz"
    local file_size=$(du -h "$compressed_file" | cut -f1)
    
    log_success "镜像导出完成"
    log_info "文件位置: $compressed_file"
    log_info "文件大小: $file_size"
    
    # 生成导入脚本
    generate_import_script "$compressed_file"
}

# 生成导入脚本
generate_import_script() {
    local image_file="$1"
    local import_script="$EXPORT_DIR/import_image.sh"
    
    log_info "生成导入脚本: $import_script"
    
    cat > "$import_script" << 'EOF'
#!/bin/bash

# 文档转换调度系统镜像导入脚本
# 用于导入Docker镜像

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker未安装，请先安装Docker"
    exit 1
fi

# 查找镜像文件
IMAGE_FILE=$(find . -name "document-scheduler_*.tar.gz" | head -1)

if [ -z "$IMAGE_FILE" ]; then
    log_error "未找到镜像文件 (document-scheduler_*.tar.gz)"
    exit 1
fi

log_info "找到镜像文件: $IMAGE_FILE"

# 解压并导入镜像
log_info "解压镜像文件..."
gunzip -c "$IMAGE_FILE" | docker load

log_success "镜像导入完成"

# 显示导入的镜像
log_info "已导入的镜像:"
docker images | grep document-scheduler

log_success "现在可以使用以下命令启动服务:"
echo "  docker run -d --name document-scheduler -p 8000:8000 document-scheduler:latest"
EOF

    chmod +x "$import_script"
    log_success "导入脚本生成完成"
}

# 生成部署包
create_deployment_package() {
    log_info "创建完整部署包..."
    
    local package_dir="$EXPORT_DIR/document-scheduler-deployment-${VERSION}"
    mkdir -p "$package_dir"
    
    # 复制必要文件
    cp docker-compose.document-scheduler.yml "$package_dir/"
    cp .env.example "$package_dir/"
    cp deploy.sh "$package_dir/"
    cp -r docs "$package_dir/"
    
    # 复制镜像文件
    cp "$EXPORT_DIR"/*.tar.gz "$package_dir/" 2>/dev/null || true
    cp "$EXPORT_DIR"/import_image.sh "$package_dir/" 2>/dev/null || true
    
    # 创建README
    cat > "$package_dir/README.md" << EOF
# 文档转换调度系统部署包

## 快速部署

1. 导入Docker镜像:
   \`\`\`bash
   ./import_image.sh
   \`\`\`

2. 配置环境变量:
   \`\`\`bash
   cp .env.example .env
   # 编辑 .env 文件根据需要修改配置
   \`\`\`

3. 启动服务:
   \`\`\`bash
   ./deploy.sh start
   \`\`\`

4. 检查服务状态:
   \`\`\`bash
   ./deploy.sh health
   \`\`\`

## 文档

- 详细部署指南: docs/deployment.md
- API接口文档: docs/api_interface.md
- Docker镜像使用指南: docs/docker_image_guide.md

## 版本信息

- 版本: ${VERSION}
- 构建时间: $(date)
- 镜像大小: $(docker images document-scheduler:latest --format "{{.Size}}")
EOF

    # 打包
    local package_file="document-scheduler-deployment-${VERSION}_${TIMESTAMP}.tar.gz"
    tar -czf "$package_file" -C "$EXPORT_DIR" "document-scheduler-deployment-${VERSION}"
    
    local package_size=$(du -h "$package_file" | cut -f1)
    
    log_success "部署包创建完成"
    log_info "部署包位置: $package_file"
    log_info "部署包大小: $package_size"
}

# 显示帮助信息
show_help() {
    echo "文档转换调度系统镜像导出脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  export    导出Docker镜像"
    echo "  package   创建完整部署包"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 export     # 导出镜像"
    echo "  $0 package    # 创建部署包"
}

# 主函数
main() {
    check_docker
    
    case "${1:-export}" in
        export)
            export_image
            ;;
        package)
            export_image
            create_deployment_package
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
