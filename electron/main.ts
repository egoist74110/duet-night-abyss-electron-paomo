import { app, BrowserWindow, globalShortcut, dialog } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { exec } from 'child_process'

// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

// 检查是否以管理员权限运行
function isAdmin(): boolean {
  if (process.platform === 'win32') {
    try {
      // 在Windows上,尝试访问需要管理员权限的注册表项
      const { execSync } = require('child_process')
      execSync('net session', { stdio: 'ignore' })
      return true
    } catch {
      return false
    }
  }
  // 其他平台暂不处理
  return true
}

// 请求管理员权限并重启应用
function requestAdminAndRestart() {
  const options = {
    type: 'warning' as const,
    buttons: ['以管理员身份重启', '退出应用'],
    defaultId: 0,
    title: '需要管理员权限',
    message: 'DNA Automator 需要管理员权限才能正常工作',
    detail: '应用需要管理员权限来:\n' +
            '• 置顶游戏窗口\n' +
            '• 模拟鼠标和键盘操作\n' +
            '• 注册全局快捷键\n\n' +
            '点击"以管理员身份重启"将关闭当前应用并以管理员权限重新启动。'
  }

  dialog.showMessageBoxSync(options)
  
  if (options.buttons[0]) {
    // 用户选择重启
    const exePath = process.execPath
    const args = process.argv.slice(1)
    
    if (process.platform === 'win32') {
      // Windows: 使用PowerShell以管理员身份启动
      const command = `Start-Process -FilePath "${exePath}" -ArgumentList "${args.join(' ')}" -Verb RunAs`
      exec(`powershell -Command "${command}"`, (error) => {
        if (error) {
          console.error('Failed to restart as admin:', error)
        }
        app.quit()
      })
    } else {
      app.quit()
    }
  } else {
    // 用户选择退出
    app.quit()
  }
}

let win: BrowserWindow | null = null

// 配置文件路径
const getConfigPath = () => {
  const userDataPath = app.getPath('userData')
  // 确保目录存在
  if (!existsSync(userDataPath)) {
    mkdirSync(userDataPath, { recursive: true })
  }
  return join(userDataPath, 'config.json')
}

// 配置接口定义
interface AppConfig {
  hotkeys: {
    start: string
    stop: string
  }
}

// 默认配置
const defaultConfig: AppConfig = {
  hotkeys: {
    start: '',
    stop: ''
  }
}

// 读取配置
function loadConfig(): AppConfig {
  try {
    const configPath = getConfigPath()
    if (existsSync(configPath)) {
      const data = readFileSync(configPath, 'utf-8')
      return JSON.parse(data)
    }
  } catch (error) {
    console.error('Failed to load config:', error)
  }
  return defaultConfig
}

// 保存配置
function saveConfig(config: AppConfig): boolean {
  try {
    const configPath = getConfigPath()
    writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8')
    console.log('Config saved to:', configPath)
    return true
  } catch (error) {
    console.error('Failed to save config:', error)
    return false
  }
}

// 注册全局快捷键
function registerHotkeys(config: AppConfig) {
  // 先注销所有快捷键
  globalShortcut.unregisterAll()

  const results = {
    start: { success: false, key: config.hotkeys.start },
    stop: { success: false, key: config.hotkeys.stop }
  }

  // 注册开始脚本快捷键
  if (config.hotkeys.start) {
    const registered = globalShortcut.register(config.hotkeys.start, () => {
      console.log('Start hotkey pressed:', config.hotkeys.start)
      if (win) {
        win.webContents.send('hotkey-triggered', 'start')
      }
    })
    results.start.success = registered
    if (registered) {
      console.log('Start hotkey registered:', config.hotkeys.start)
    } else {
      console.error('Failed to register start hotkey:', config.hotkeys.start)
    }
  }

  // 注册停止脚本快捷键
  if (config.hotkeys.stop) {
    const registered = globalShortcut.register(config.hotkeys.stop, () => {
      console.log('Stop hotkey pressed:', config.hotkeys.stop)
      if (win) {
        win.webContents.send('hotkey-triggered', 'stop')
      }
    })
    results.stop.success = registered
    if (registered) {
      console.log('Stop hotkey registered:', config.hotkeys.stop)
    } else {
      console.error('Failed to register stop hotkey:', config.hotkeys.stop)
    }
  }

  // 通知前端注册结果
  if (win) {
    win.webContents.send('hotkey-registration-result', results)
  }

  return results
}

function createWindow() {
  const preloadPath = join(__dirname, 'preload.js')

  win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: preloadPath,
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false
    },
    titleBarStyle: 'hidden',
  })

  // 开发模式加载 Vite 开发服务器,生产模式加载打包后的文件
  if (!app.isPackaged) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools()
  } else {
    win.loadURL(`file://${join(__dirname, '../dist/index.html')}`)
  }
}

app.on('window-all-closed', () => {
  killPythonEngine()
  if (process.platform !== 'darwin') app.quit()
})

// --- Python Engine Management ---
import { spawn, ChildProcess } from 'child_process'

let pyProc: ChildProcess | null = null
let pythonOutputBuffer = '' // 缓冲区用于处理不完整的JSON

function startPythonEngine() {
  // 优先使用嵌入式Python，如果不存在则使用系统Python
  const embeddedPythonPath = join(__dirname, '../python/python.exe')
  const systemPythonPath = 'python'

  // 检查嵌入式Python是否存在
  const fs = require('fs')
  const pythonPath = fs.existsSync(embeddedPythonPath) ? embeddedPythonPath : systemPythonPath

  // Fix: __dirname is dist-electron. We need to go up one level to root, then into py_engine.
  const scriptPath = join(__dirname, '../py_engine/main.py')

  console.log(`Using Python: ${pythonPath}`)
  console.log(`Starting Python engine at: ${scriptPath}`)

  // 重置缓冲区
  pythonOutputBuffer = ''

  pyProc = spawn(pythonPath, [scriptPath])

  pyProc.stdout?.on('data', (data: Buffer) => {
    const str = data.toString()
    console.log('[Python Raw]', str)

    // 将新数据添加到缓冲区
    pythonOutputBuffer += str

    // 按行分割处理
    const lines = pythonOutputBuffer.split('\n')

    // 保留最后一个可能不完整的行
    pythonOutputBuffer = lines.pop() || ''

    // 处理完整的行
    lines.forEach((line: string) => {
      if (!line.trim()) return
      try {
        const json = JSON.parse(line)
        if (win) {
          win.webContents.send('python-data', json)
        }
      } catch (e) {
        console.log('[Python Non-JSON]', line)
      }
    })
  })

  pyProc.stderr?.on('data', (data: Buffer) => {
    console.error(`[Python Err]: ${data}`)
    // 也将错误信息发送到前端日志
    if (win) {
      win.webContents.send('python-data', {
        type: 'log',
        data: {
          level: 'ERROR',
          message: `Python stderr: ${data.toString()}`,
          timestamp: Date.now() / 1000
        }
      })
    }
  })

  pyProc.on('close', (code: number) => {
    console.log(`Python process exited with code ${code}`)
    if (win) {
      win.webContents.send('python-data', {
        type: 'log',
        data: {
          level: 'WARN',
          message: `Python process exited with code ${code}`,
          timestamp: Date.now() / 1000
        }
      })
    }
    pyProc = null
    pythonOutputBuffer = ''
  })

  pyProc.on('error', (error: Error) => {
    console.error('Failed to start Python process:', error)
    if (win) {
      win.webContents.send('python-data', {
        type: 'log',
        data: {
          level: 'ERROR',
          message: `Failed to start Python: ${error.message}`,
          timestamp: Date.now() / 1000
        }
      })
    }
  })
}

function killPythonEngine() {
  if (pyProc) {
    pyProc.kill()
    pyProc = null
  }
}

// 监听渲染进程发送的消息转发给 Python
import { ipcMain, IpcMainEvent } from 'electron'
ipcMain.on('to-python', (event: IpcMainEvent, arg: any) => {
  if (pyProc && pyProc.stdin) {
    const data = JSON.stringify(arg) + '\n'
    pyProc.stdin.write(data)
  }
})

// 处理 ping 请求
ipcMain.handle('ping', async () => {
  console.log('Received ping from renderer')
  return 'pong from main'
})

// 处理保存配置请求
ipcMain.handle('save-config', async (event, config: AppConfig) => {
  const success = saveConfig(config)
  if (success) {
    // 重新注册快捷键
    registerHotkeys(config)
  }
  return success
})

// 处理加载配置请求
ipcMain.handle('load-config', async () => {
  return loadConfig()
})

// 应用启动
app.whenReady().then(() => {
  console.log('App is ready, checking admin privileges...')
  
  // 检查管理员权限
  if (!isAdmin()) {
    console.warn('Application is not running with administrator privileges')
    requestAdminAndRestart()
    return
  }
  
  console.log('Running with administrator privileges ✓')
  console.log('Creating window...')
  
  createWindow()
  startPythonEngine()

  // 加载配置并注册快捷键
  const config = loadConfig()
  registerHotkeys(config)

  app.on('activate', () => {
    // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// 应用退出时注销所有快捷键
app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})
