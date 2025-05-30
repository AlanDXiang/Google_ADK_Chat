# Google ADK Chat Makefile
.PHONY: help install dev test lint format clean run docker-build docker-run docker-stop docs

# 默认目标
.DEFAULT_GOAL := help

# 项目变量
PROJECT_NAME := google-adk-chat
PYTHON := python
PIP := pip
DOCKER_IMAGE := $(PROJECT_NAME):latest
DOCKER_CONTAINER := $(PROJECT_NAME)-container

help: ## 显示帮助信息
	@echo "Google ADK Chat - 可用命令："
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# 环境设置
install: ## 安装项目依赖
	$(PIP) install -r requirements.txt

install-dev: ## 安装开发依赖
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[dev]

setup: ## 初始设置（创建环境文件等）
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "已创建 .env 文件，请编辑其中的配置"; \
	else \
		echo ".env 文件已存在"; \
	fi
	@mkdir -p logs
	@echo "初始设置完成"

# 开发相关
dev: setup ## 启动开发环境
	$(PYTHON) main.py

run: ## 运行应用
	$(PYTHON) main.py

debug: ## 调试模式运行
	DEBUG_MODE=true $(PYTHON) main.py

# 测试相关
test: ## 运行所有测试
	pytest

test-unit: ## 运行单元测试
	pytest -m "unit"

test-integration: ## 运行集成测试
	pytest -m "integration"

test-coverage: ## 运行测试并生成覆盖率报告
	pytest --cov=src --cov-report=html --cov-report=term

test-watch: ## 监视模式运行测试
	pytest-watch

# 代码质量
lint: ## 代码检查
	flake8 src tests
	mypy src

format: ## 代码格式化
	black src tests
	isort src tests

format-check: ## 检查代码格式
	black --check src tests
	isort --check-only src tests

# 清理
clean: ## 清理生成的文件
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-logs: ## 清理日志文件
	rm -rf logs/*.log

# Docker相关
docker-build: ## 构建Docker镜像
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## 运行Docker容器
	docker run -d \
		--name $(DOCKER_CONTAINER) \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		$(DOCKER_IMAGE)

docker-stop: ## 停止并删除Docker容器
	docker stop $(DOCKER_CONTAINER) || true
	docker rm $(DOCKER_CONTAINER) || true

docker-logs: ## 查看Docker容器日志
	docker logs -f $(DOCKER_CONTAINER)

docker-shell: ## 进入Docker容器shell
	docker exec -it $(DOCKER_CONTAINER) /bin/bash

# Docker Compose相关
compose-up: ## 启动Docker Compose服务
	docker-compose up -d

compose-down: ## 停止Docker Compose服务
	docker-compose down

compose-logs: ## 查看Docker Compose日志
	docker-compose logs -f

compose-build: ## 构建Docker Compose服务
	docker-compose build

# 部署相关
deploy-dev: ## 部署到开发环境
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

deploy-prod: ## 部署到生产环境
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 数据库/缓存相关
redis-start: ## 启动Redis服务
	docker-compose --profile with-redis up -d redis

redis-stop: ## 停止Redis服务
	docker-compose stop redis

redis-cli: ## 连接Redis CLI
	docker-compose exec redis redis-cli

# 监控和健康检查
health-check: ## 健康检查
	curl -f http://localhost:8000/api/health || echo "服务不可用"

status: ## 查看服务状态
	@echo "检查服务状态..."
	@curl -s http://localhost:8000/api/health | python -m json.tool || echo "服务未运行"

# 文档相关
docs-serve: ## 启动文档服务器
	@echo "文档服务器启动中..."
	@echo "API文档: http://localhost:8000/docs"
	@echo "项目文档请查看 docs/ 目录"

docs-build: ## 构建文档
	@echo "构建文档..."
	@echo "文档位于 docs/ 目录"

# 工具相关
tools-list: ## 列出可用工具
	curl -s http://localhost:8000/api/tools | python -m json.tool

tools-test: ## 测试工具功能
	curl -s -X POST http://localhost:8000/api/tools/echo/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"text": "Hello World", "repeat": 2}}' | python -m json.tool

# 性能测试
benchmark: ## 运行性能测试
	@echo "运行性能测试..."
	@echo "需要安装 ab (Apache Benchmark) 工具"
	ab -n 100 -c 10 http://localhost:8000/api/health

load-test: ## 负载测试
	@echo "运行负载测试..."
	@echo "需要安装 wrk 工具"
	wrk -t12 -c400 -d30s http://localhost:8000/api/health

# 备份和恢复
backup: ## 备份数据
	@echo "备份配置和日志..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz .env logs/

restore: ## 恢复数据（需要指定备份文件）
	@echo "请提供备份文件: make restore FILE=backup-20240101-120000.tar.gz"

# 安全检查
security-check: ## 安全检查
	@echo "运行安全检查..."
	$(PIP) install safety bandit
	safety check
	bandit -r src/

# 项目初始化
init: install-dev setup ## 初始化项目（首次使用）
	@echo "项目初始化完成！"
	@echo "请编辑 .env 文件设置您的配置"
	@echo "然后运行: make dev"

# 更新依赖
update-deps: ## 更新依赖包
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements.txt

freeze-deps: ## 冻结当前依赖版本
	$(PIP) freeze > requirements-freeze.txt

# 版本管理
version: ## 显示版本信息
	@echo "项目版本: $(shell grep version pyproject.toml | head -1 | cut -d'"' -f2)"
	@echo "Python版本: $(shell python --version)"
	@echo "依赖包版本:"
	@$(PIP) list | grep -E "(fastapi|uvicorn|litellm)"

# 一键命令
all: clean install-dev test lint ## 完整检查（清理、安装、测试、检查）

quick-start: init dev ## 快速开始（适合新用户） 