# Python后端架构说明

## 🎯 设计目标

重构后的Python后端采用现代化的面向对象设计，遵循SOLID原则，实现了高内聚、低耦合的服务化架构。

## 🏗️ 架构概览

### 核心设计原则

1. **单一职责原则 (SRP)**: 每个类和服务只负责一个功能
2. **开闭原则 (OCP)**: 对扩展开放，对修改关闭
3. **里氏替换原则 (LSP)**: 子类可以替换父类
4. **接口隔离原则 (ISP)**: 使用多个专门的接口
5. **依赖倒置原则 (DIP)**: 依赖抽象而不是具体实现

### 架构层次

```
┌─────────────────────────────────────────┐
│              主入口层 (main.py)           │
│        DNAAutomatorEngine               │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│              命令路由层                   │
│     CommandRouter + CommandHandlers     │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│              服务管理层                   │
│          ServiceManager                 │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│              业务服务层                   │
│   WindowService + ScriptService         │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│              基础模块层                   │
│  WindowCapture + ImageRecognition       │
└─────────────────────────────────────────┘
```

## 📦 模块详解

### 1. 核心模块 (core/)

#### BaseService (base_service.py)
- **职责**: 定义所有服务的基类和通用行为
- **功能**: 
  - 服务生命周期管理（初始化、启动、停止）
  - 统一的日志记录和错误处理
  - 配置管理和状态查询
- **设计模式**: 模板方法模式、策略模式

#### ServiceManager (base_service.py)
- **职责**: 管理所有服务的注册、初始化和生命周期
- **功能**:
  - 服务注册和依赖管理
  - 按依赖顺序初始化服务
  - 统一的服务状态查询
- **设计模式**: 单例模式、工厂模式

#### CommandRouter (command_handler.py)
- **职责**: 命令路由和分发
- **功能**:
  - 命令验证和参数检查
  - 路由到对应的处理器
  - 统一的错误处理和响应
- **设计模式**: 命令模式、责任链模式

### 2. 业务服务层 (services/)

#### WindowService (window_service.py)
- **职责**: 游戏窗口的所有操作
- **功能**:
  - 窗口检测和枚举
  - 窗口连接和设置
  - 窗口激活和置顶
  - 窗口截图和状态管理
- **依赖**: WindowCapture

#### ScriptService (script_service.py)
- **职责**: 游戏自动化脚本的执行和管理
- **功能**:
  - 脚本生命周期管理
  - 脚本状态监控和统计
  - 脚本暂停和恢复
  - 脚本配置管理
- **依赖**: WindowService, ImageRecognition

### 3. 命令处理器

每个服务都有对应的命令处理器，负责：
- 处理特定领域的命令
- 参数验证和转换
- 调用服务方法
- 格式化响应数据

## 🔄 数据流

### 命令处理流程

```
Electron前端
    │ JSON命令
    ▼
DNAAutomatorEngine.process_command()
    │
    ▼
CommandRouter.route_command()
    │ 验证命令格式
    ▼
CommandValidator.validate_command()
    │ 路由到处理器
    ▼
XxxCommandHandler.handle_command()
    │ 调用服务方法
    ▼
XxxService.method()
    │ 返回结果
    ▼
响应发送到前端
```

### 服务初始化流程

```
DNAAutomatorEngine.initialize()
    │
    ▼
创建服务实例
    │
    ▼
ServiceManager.register_service()
    │
    ▼
ServiceManager.initialize_all_services()
    │ 按依赖顺序初始化
    ▼
各服务的initialize()方法
    │
    ▼
设置服务依赖关系
    │
    ▼
注册命令处理器
```

## 🎨 设计模式应用

### 1. 模板方法模式
- **应用**: BaseService定义服务生命周期模板
- **优势**: 统一服务行为，子类只需实现具体逻辑

### 2. 命令模式
- **应用**: CommandRouter和CommandHandler
- **优势**: 解耦命令发送者和接收者，支持命令队列和撤销

### 3. 策略模式
- **应用**: 不同的服务实现不同的业务策略
- **优势**: 算法可以独立变化，易于扩展

### 4. 依赖注入
- **应用**: 服务之间通过构造函数或setter注入依赖
- **优势**: 降低耦合度，便于测试和扩展

### 5. 工厂模式
- **应用**: ServiceManager创建和管理服务实例
- **优势**: 集中管理对象创建，支持配置化

## 🚀 扩展指南

### 添加新服务

1. **创建服务类**:
```python
class NewService(BaseService):
    def __init__(self):
        super().__init__("NewService")
    
    def initialize(self, config=None):
        # 初始化逻辑
        pass
    
    def start(self):
        # 启动逻辑
        pass
    
    def stop(self):
        # 停止逻辑
        pass
    
    def get_status(self):
        # 状态查询
        pass
```

2. **创建命令处理器**:
```python
class NewCommandHandler(BaseCommandHandler):
    def __init__(self, new_service):
        super().__init__("NewCommandHandler")
        self.new_service = new_service
    
    def get_supported_actions(self):
        return ['new_action1', 'new_action2']
    
    def handle_command(self, action, cmd):
        # 处理命令逻辑
        pass
```

3. **注册服务和处理器**:
```python
# 在DNAAutomatorEngine._create_services()中
new_service = NewService()
self.service_manager.register_service(new_service, dependencies=["WindowService"])

# 在DNAAutomatorEngine._register_command_handlers()中
new_handler = NewCommandHandler(new_service)
self.command_router.register_handler(new_handler)
```

### 添加新命令

1. **在对应的CommandHandler中添加命令**:
```python
def get_supported_actions(self):
    return ['existing_action', 'new_action']  # 添加新命令

def handle_command(self, action, cmd):
    if action == 'new_action':
        return self._handle_new_action(cmd)
    # ... 其他命令处理

def _handle_new_action(self, cmd):
    # 新命令的处理逻辑
    pass
```

## 🔍 调试和监控

### 日志系统
- 每个服务都有统一的日志接口
- 日志包含服务名称、时间戳、级别等信息
- 支持不同级别的日志过滤

### 状态监控
- 每个服务都提供状态查询接口
- ServiceManager提供全局状态查询
- 支持实时状态监控和诊断

### 错误处理
- 统一的错误处理机制
- 详细的错误上下文和堆栈信息
- 错误自动上报到前端

## 📈 性能优化

### 异步处理
- 脚本执行在独立线程中运行
- 支持脚本暂停和恢复
- 避免阻塞主线程

### 资源管理
- 服务生命周期管理确保资源正确释放
- 支持服务的优雅停止
- 内存和线程资源的合理使用

### 配置优化
- 支持运行时配置更新
- 配置验证和默认值处理
- 性能相关参数的动态调整

## 🧪 测试策略

### 单元测试
- 每个服务可以独立测试
- 依赖注入便于Mock测试
- 命令处理器可以单独测试

### 集成测试
- 服务之间的协作测试
- 完整命令流程测试
- 错误场景测试

### 性能测试
- 服务启动时间测试
- 命令处理性能测试
- 内存使用情况测试

这个架构为项目提供了坚实的基础，支持未来的功能扩展和维护。