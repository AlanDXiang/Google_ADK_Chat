/**
 * Google ADK Chat 前端应用
 * 
 * 实现聊天界面、工具管理、配置显示等功能
 */

class ADKChatApp {
    constructor() {
        this.config = null;
        this.streamMode = false;
        this.includeHistory = true;
        this.currentWebSocket = null;
        this.toolsData = null;
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.loadConfig();
        await this.loadTools();
        this.updateStatus();
    }
    
    setupEventListeners() {
        // 发送消息
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // 清空对话
        document.getElementById('clearBtn').addEventListener('click', () => this.clearChat());
        
        // 切换模式
        document.getElementById('streamToggle').addEventListener('click', () => this.toggleStreamMode());
        document.getElementById('historyToggle').addEventListener('click', () => this.toggleHistoryMode());
        
        // 导航按钮
        document.getElementById('toolsBtn').addEventListener('click', () => this.toggleToolsPanel());
        document.getElementById('configBtn').addEventListener('click', () => this.showConfigModal());
        
        // 工具执行
        document.getElementById('executeToolBtn').addEventListener('click', () => this.executeTool());
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                this.config = await response.json();
                this.updateModelInfo();
            } else {
                console.error('加载配置失败:', response.statusText);
            }
        } catch (error) {
            console.error('加载配置出错:', error);
        }
    }
    
    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            if (response.ok) {
                const result = await response.json();
                this.toolsData = result.data;
                this.renderToolsList();
            } else {
                console.error('加载工具失败:', response.statusText);
            }
        } catch (error) {
            console.error('加载工具出错:', error);
        }
    }
    
    updateStatus() {
        const statusBadge = document.getElementById('statusBadge');
        if (this.config && this.config.api_key_configured) {
            statusBadge.innerHTML = '<i class="bi bi-circle-fill"></i> 在线';
            statusBadge.className = 'badge bg-success';
        } else {
            statusBadge.innerHTML = '<i class="bi bi-circle-fill"></i> 配置未完成';
            statusBadge.className = 'badge bg-warning';
        }
    }
    
    updateModelInfo() {
        const modelInfo = document.getElementById('modelInfo');
        if (this.config) {
            modelInfo.textContent = `模型: ${this.config.llm_model} | 流式: ${this.streamMode ? '开启' : '关闭'} | 历史: ${this.includeHistory ? '开启' : '关闭'}`;
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // 检查配置
        if (!this.config || !this.config.api_key_configured) {
            this.showAlert('请先配置API密钥', 'warning');
            return;
        }
        
        // 清空输入框
        input.value = '';
        
        // 显示用户消息
        this.addMessage('user', message);
        
        // 显示加载状态
        const loadingId = this.showTypingIndicator();
        
        try {
            if (this.streamMode) {
                await this.sendStreamMessage(message);
            } else {
                await this.sendNormalMessage(message);
            }
        } catch (error) {
            console.error('发送消息出错:', error);
            this.showAlert('发送消息失败: ' + error.message, 'danger');
        } finally {
            this.hideTypingIndicator(loadingId);
        }
    }
    
    async sendNormalMessage(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                include_history: this.includeHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        if (result.success) {
            this.addMessage('assistant', result.data.content, result.data);
        } else {
            throw new Error(result.error || '未知错误');
        }
    }
    
    async sendStreamMessage(message) {
        return new Promise((resolve, reject) => {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/api/chat/stream`;
            
            this.currentWebSocket = new WebSocket(wsUrl);
            let assistantMessage = '';
            let messageElement = null;
            
            this.currentWebSocket.onopen = () => {
                // 发送消息
                this.currentWebSocket.send(JSON.stringify({
                    message: message,
                    include_history: this.includeHistory
                }));
            };
            
            this.currentWebSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'start':
                        messageElement = this.addMessage('assistant', '', null, true);
                        break;
                    case 'chunk':
                        assistantMessage += data.content;
                        this.updateMessage(messageElement, assistantMessage);
                        break;
                    case 'end':
                        this.finalizeMessage(messageElement);
                        resolve();
                        break;
                    case 'error':
                        reject(new Error(data.message));
                        break;
                }
            };
            
            this.currentWebSocket.onerror = (error) => {
                reject(new Error('WebSocket连接错误'));
            };
            
            this.currentWebSocket.onclose = () => {
                this.currentWebSocket = null;
            };
        });
    }
    
    addMessage(role, content, metadata = null, isStreaming = false) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // 隐藏欢迎消息
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} fade-in`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant' && !isStreaming) {
            contentDiv.innerHTML = this.formatContent(content);
        } else {
            contentDiv.textContent = content;
        }
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        
        const timeSpan = document.createElement('span');
        timeSpan.textContent = new Date().toLocaleTimeString();
        metaDiv.appendChild(timeSpan);
        
        if (metadata) {
            if (metadata.response_time) {
                const timeInfo = document.createElement('span');
                timeInfo.textContent = `${(metadata.response_time * 1000).toFixed(0)}ms`;
                metaDiv.appendChild(timeInfo);
            }
            
            if (metadata.usage && metadata.usage.total_tokens) {
                const tokenInfo = document.createElement('span');
                tokenInfo.textContent = `${metadata.usage.total_tokens} tokens`;
                metaDiv.appendChild(tokenInfo);
            }
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        contentDiv.appendChild(metaDiv);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageDiv;
    }
    
    updateMessage(messageElement, content) {
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            contentDiv.innerHTML = this.formatContent(content);
            
            // 滚动到底部
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    finalizeMessage(messageElement) {
        // 消息完成后的处理
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            const content = contentDiv.textContent || contentDiv.innerText;
            contentDiv.innerHTML = this.formatContent(content);
        }
    }
    
    formatContent(content) {
        // 使用marked库解析Markdown
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        } else {
            // 简单的文本格式化
            return content
                .replace(/\n/g, '<br>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>');
        }
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.id = 'typing-indicator-' + Date.now();
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="bi bi-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        loadingDiv.appendChild(avatar);
        loadingDiv.appendChild(contentDiv);
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return loadingDiv.id;
    }
    
    hideTypingIndicator(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
    
    async clearChat() {
        try {
            const response = await fetch('/api/chat/clear', { method: 'POST' });
            if (response.ok) {
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <div class="text-center p-4">
                            <i class="bi bi-robot fs-1 text-primary"></i>
                            <h3 class="mt-3">对话已清空</h3>
                            <p class="text-muted">您可以开始新的对话</p>
                        </div>
                    </div>
                `;
                this.showAlert('对话历史已清空', 'success');
            }
        } catch (error) {
            console.error('清空对话出错:', error);
            this.showAlert('清空对话失败', 'danger');
        }
    }
    
    toggleStreamMode() {
        this.streamMode = !this.streamMode;
        const btn = document.getElementById('streamToggle');
        
        if (this.streamMode) {
            btn.classList.add('active');
            btn.title = '关闭流式模式';
        } else {
            btn.classList.remove('active');
            btn.title = '开启流式模式';
        }
        
        this.updateModelInfo();
    }
    
    toggleHistoryMode() {
        this.includeHistory = !this.includeHistory;
        const btn = document.getElementById('historyToggle');
        
        if (this.includeHistory) {
            btn.classList.add('active');
            btn.title = '关闭历史模式';
        } else {
            btn.classList.remove('active');
            btn.title = '开启历史模式';
        }
        
        this.updateModelInfo();
    }
    
    toggleToolsPanel() {
        const sidePanel = document.getElementById('sidePanel');
        const mainPanel = document.getElementById('mainPanel');
        
        if (sidePanel.style.display === 'none') {
            sidePanel.style.display = 'block';
            mainPanel.className = 'col-md-9';
        } else {
            sidePanel.style.display = 'none';
            mainPanel.className = 'col-md-12';
        }
    }
    
    renderToolsList() {
        const toolsList = document.getElementById('toolsList');
        
        if (!this.toolsData || !this.toolsData.tools) {
            toolsList.innerHTML = '<p class="text-muted">暂无可用工具</p>';
            return;
        }
        
        const tools = Object.values(this.toolsData.tools);
        if (tools.length === 0) {
            toolsList.innerHTML = '<p class="text-muted">暂无可用工具</p>';
            return;
        }
        
        toolsList.innerHTML = tools.map(tool => `
            <div class="tool-item" onclick="app.showToolModal('${tool.name}')">
                <h6>${tool.name}</h6>
                <small>${tool.description}</small>
                <div class="mt-2">
                    <span class="badge bg-secondary tool-badge">${tool.type}</span>
                    <span class="badge bg-primary tool-badge">v${tool.version}</span>
                </div>
            </div>
        `).join('');
    }
    
    showToolModal(toolName) {
        const tool = this.toolsData.tools[toolName];
        if (!tool) return;
        
        const modal = new bootstrap.Modal(document.getElementById('toolModal'));
        const modalTitle = document.querySelector('#toolModal .modal-title');
        const toolForm = document.getElementById('toolExecuteForm');
        
        modalTitle.innerHTML = `<i class="bi bi-play-circle"></i> 执行工具: ${tool.name}`;
        
        // 生成表单
        toolForm.innerHTML = `
            <div class="mb-3">
                <h6>${tool.name}</h6>
                <p class="text-muted">${tool.description}</p>
            </div>
            <form id="toolExecuteForm">
                ${tool.parameters.map(param => `
                    <div class="tool-form-group">
                        <label for="param_${param.name}" class="form-label">
                            ${param.name}
                            ${param.required ? '<span class="text-danger">*</span>' : ''}
                        </label>
                        <input 
                            type="${this.getInputType(param.type)}" 
                            class="form-control" 
                            id="param_${param.name}" 
                            name="${param.name}"
                            ${param.required ? 'required' : ''}
                            ${param.default !== null ? `value="${param.default}"` : ''}
                        >
                        <div class="form-text">${param.description}</div>
                    </div>
                `).join('')}
            </form>
            <div id="toolResult"></div>
        `;
        
        // 存储当前工具名称
        document.getElementById('executeToolBtn').dataset.toolName = toolName;
        
        modal.show();
    }
    
    getInputType(paramType) {
        switch (paramType) {
            case 'int':
            case 'float':
                return 'number';
            case 'bool':
                return 'checkbox';
            default:
                return 'text';
        }
    }
    
    async executeTool() {
        const btn = document.getElementById('executeToolBtn');
        const toolName = btn.dataset.toolName;
        const form = document.getElementById('toolExecuteForm');
        const resultDiv = document.getElementById('toolResult');
        
        // 获取表单数据
        const formData = new FormData(form);
        const parameters = {};
        
        for (const [key, value] of formData.entries()) {
            parameters[key] = value;
        }
        
        // 设置加载状态
        btn.classList.add('btn-loading');
        btn.disabled = true;
        
        try {
            const response = await fetch(`/api/tools/${toolName}/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parameters })
            });
            
            const result = await response.json();
            
            // 显示结果
            resultDiv.innerHTML = `
                <div class="tool-result ${result.success ? 'success' : 'error'}">
                    <h6>${result.success ? '执行成功' : '执行失败'}</h6>
                    ${result.error ? `<p class="text-danger">${result.error}</p>` : ''}
                    ${result.data ? `<pre>${JSON.stringify(result.data, null, 2)}</pre>` : ''}
                </div>
            `;
            
            if (result.success) {
                this.showAlert('工具执行成功', 'success');
            } else {
                this.showAlert('工具执行失败: ' + result.error, 'danger');
            }
            
        } catch (error) {
            console.error('执行工具出错:', error);
            resultDiv.innerHTML = `
                <div class="tool-result error">
                    <h6>执行出错</h6>
                    <p class="text-danger">${error.message}</p>
                </div>
            `;
            this.showAlert('工具执行出错: ' + error.message, 'danger');
        } finally {
            btn.classList.remove('btn-loading');
            btn.disabled = false;
        }
    }
    
    async showConfigModal() {
        const modal = new bootstrap.Modal(document.getElementById('configModal'));
        const configContent = document.getElementById('configContent');
        
        if (this.config) {
            configContent.innerHTML = `
                <div class="config-card card">
                    <div class="card-header">模型配置</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>模型:</strong> ${this.config.llm_model}
                            </div>
                            <div class="col-md-6">
                                <strong>API基础URL:</strong> ${this.config.llm_base_url}
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-md-6">
                                <strong>API密钥:</strong> 
                                <span class="badge ${this.config.api_key_configured ? 'bg-success' : 'bg-danger'}">
                                    ${this.config.api_key_configured ? '已配置' : '未配置'}
                                </span>
                            </div>
                            <div class="col-md-6">
                                <strong>调试模式:</strong> 
                                <span class="badge ${this.config.debug_mode ? 'bg-info' : 'bg-secondary'}">
                                    ${this.config.debug_mode ? '开启' : '关闭'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="config-card card">
                    <div class="card-header">工具配置</div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>工具目录:</strong> ${this.config.tools_directory}
                            </div>
                            <div class="col-md-6">
                                <strong>已加载工具:</strong> ${this.toolsData ? this.toolsData.count : 0} 个
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    <strong>配置说明:</strong>
                    <ul class="mb-0 mt-2">
                        <li>修改配置请编辑 <code>.env</code> 文件或设置环境变量</li>
                        <li>环境变量的优先级高于 <code>.env</code> 文件</li>
                        <li>修改配置后需要重启应用才能生效</li>
                    </ul>
                </div>
            `;
        } else {
            configContent.innerHTML = '<div class="alert alert-warning">配置加载失败</div>';
        }
        
        modal.show();
    }
    
    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-floating alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // 自动移除
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ADKChatApp();
}); 