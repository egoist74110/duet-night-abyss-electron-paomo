import { app, BrowserWindow, globalShortcut } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'

// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

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

  // 注册开始脚本快捷键
  if (config.hotkeys.start) {
    const registered = globalShortcut.register(config.hotkeys.start, () => {
      console.log('Start hotkey pressed:', config.hotkeys.start)
      if (win) {
        win.webContents.send('hotkey-triggered', 'start')
      }
    })
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
    if (registered) {
      console.log('Stop hotkey registered:', config.hotkeys.stop)
    } else {
      console.error('Failed to register stop hotkey:', config.hotkeys.stop)
    }
  }
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

function startPythonEngine() {
  const pythonPath = 'python3' // 假设环境变量中有 python3，生产环境可能需要指向打包后的 python
  // Fix: __dirname is dist-electron. We need to go up one level to root, then into py_engine.
  const scriptPath = join(__dirname, '../py_engine/main.py') 

  console.log(`Starting Python engine at: ${scriptPath}`)
  
  pyProc = spawn(pythonPath, [scriptPath])

  pyProc.stdout?.on('data', (data: Buffer) => {
    const str = data.toString()
    console.log('[Python Raw]', str)
    try {
      // Python 可能会一次输出多行，或者分块输出。这里做简单的按行分割处理。
      // 实际生产中可能需要更健壮的缓冲区处理。
      const lines = str.split('\n')
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
    } catch (e) {
      console.error('Error parsing python output:', e)
    }
  })

  pyProc.stderr?.on('data', (data: Buffer) => {
    console.error(`[Python Err]: ${data}`)
  })

  pyProc.on('close', (code: number) => {
    console.log(`Python process exited with code ${code}`)
    pyProc = null
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
  console.log('App is ready, creating window...')
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
