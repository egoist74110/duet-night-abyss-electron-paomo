import { app, BrowserWindow, globalShortcut, dialog } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { exec } from 'child_process'

// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

// 项目配置接口
interface ProjectConfig {
  name: string
  displayName: string
  version: string
  description: string
  author: string
  keywords: string[]
  platforms: {
    [key: string]: {
      adminRequired: boolean
      adminMessage: string
    }
  }
}

// 读取项目配置
function loadProjectConfig(): ProjectConfig {
  try {
    const configPath = app.isPackaged
      ? join(process.resourcesPath, 'project.config.json')
      : join(__dirname, '../project.config.json')
    
    if (existsSync(configPath)) {
      const data = readFileSync(configPath, 'utf-8')
      const config = JSON.parse(data)
      console.log('Project config loaded:', config.name, config.version)
      return config
    }
  } catch (error) {
    console.error('Failed to load project config:', error)
  }
  
  // 默认配置
  return {
    name: 'DNA Automator',
    displayName: 'Duet Night Abyss Automator',
    version: '0.1.0',
    description: '基于 Electron + Vue 3 + Python 的自动化游戏辅助工具',
    author: 'DNA Team',
    keywords: ['游戏自动化', '图像识别', '脚本引擎'],
    platforms: {
      win32: {
        adminRequired: true,
        adminMessage: '需要管理员权限来置顶窗口、注册全局快捷键和模拟鼠标键盘操作'
      },
      darwin: {
        adminRequired: false,
        adminMessage: '需要辅助功能权限来操作窗口和模拟用户输入'
      },
      linux: {
        adminRequired: false,
        adminMessage: '需要X11权限和输入设备权限来操作窗口和模拟用户输入'
      }
    }
  }
}

// 全局项目配置
const projectConfig = loadProjectConfig()

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
// 注意: 此函数暂时未使用,因为我们改为让用户手动设置管理员权限
// 保留此函数以备将来需要时使用
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

// 导出函数以避免未使用警告(将来可能需要)
export { requestAdminAndRestart }

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
  serverType?: 'cn' | 'global'
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

// 注册停止快捷键 - 只在脚本运行模式下使用
function registerStopHotkey(stopKey: string) {
  // 先注销所有快捷键
  globalShortcut.unregisterAll()

  if (!stopKey) {
    console.warn('Stop hotkey is empty, cannot register')
    return false
  }

  const registered = globalShortcut.register(stopKey, () => {
    console.log('Stop hotkey pressed:', stopKey)
    if (win) {
      win.webContents.send('hotkey-triggered', 'stop')
    }
  })

  if (registered) {
    console.log('Stop hotkey registered:', stopKey)
  } else {
    console.error('Failed to register stop hotkey:', stopKey)
  }

  return registered
}

// 注销所有快捷键
function unregisterAllHotkeys() {
  globalShortcut.unregisterAll()
  console.log('All hotkeys unregistered')
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
    // 移除 titleBarStyle: 'hidden',让窗口显示标准的标题栏和控制按钮
    // 这样用户就可以看到最小化、最大化、关闭按钮
  })

  // 移除Electron默认菜单栏(File, Edit, View等)
  // 让程序看起来更专业,不显示开发工具相关的菜单
  win.setMenu(null)

  // 开发模式加载 Vite 开发服务器并打开控制台,生产模式加载打包后的文件且不打开控制台
  if (!app.isPackaged) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools() // 只在开发模式打开控制台
  } else {
    win.loadURL(`file://${join(__dirname, '../dist/index.html')}`)
    // 生产模式不打开控制台,让程序看起来像正经的exe程序
  }
}

app.on('window-all-closed', () => {
  console.log('All windows closed, cleaning up...')
  
  // 1. 注销所有快捷键
  unregisterAllHotkeys()
  
  // 2. 发送取消置顶命令到Python(如果Python进程还在运行)
  if (pyProc && pyProc.stdin) {
    try {
      const command = JSON.stringify({ action: 'deactivate_topmost' }) + '\n'
      pyProc.stdin.write(command)
      console.log('Sent deactivate_topmost command to Python')
    } catch (error) {
      console.error('Failed to send deactivate_topmost command:', error)
    }
  }
  
  // 3. 等待一小段时间让Python处理命令
  setTimeout(() => {
    // 4. 终止Python进程
    killPythonEngine()
    
    // 5. 退出应用
    if (process.platform !== 'darwin') app.quit()
  }, 200) // 等待200ms
})

// --- Python Engine Management ---
import { spawn, ChildProcess } from 'child_process'

let pyProc: ChildProcess | null = null
let pythonOutputBuffer = '' // 缓冲区用于处理不完整的JSON

function startPythonEngine() {
  // 根据操作系统选择合适的Python路径
  let pythonPath: string
  
  if (process.platform === 'win32') {
    // Windows: 优先使用嵌入式Python，如果不存在则使用系统Python
    const embeddedPythonPath = join(__dirname, '../python/python.exe')
    const fs = require('fs')
    pythonPath = fs.existsSync(embeddedPythonPath) ? embeddedPythonPath : 'python'
  } else {
    // macOS/Linux: 尝试多个可能的Python命令
    const possiblePythonPaths = ['python3', 'python', '/usr/bin/python3', '/usr/local/bin/python3']
    pythonPath = 'python3' // 默认使用python3
    
    // 检查哪个Python命令可用
    const { execSync } = require('child_process')
    for (const path of possiblePythonPaths) {
      try {
        execSync(`${path} --version`, { stdio: 'ignore' })
        pythonPath = path
        console.log(`Found Python at: ${path}`)
        break
      } catch (error) {
        // 继续尝试下一个路径
      }
    }
  }

  // Python脚本路径
  // 开发模式: __dirname 是 dist-electron,需要回到根目录再进入 py_engine
  // 生产模式(打包后): 需要从 resources 目录读取
  const scriptPath = app.isPackaged
    ? join(process.resourcesPath, 'py_engine/main.py')
    : join(__dirname, '../py_engine/main.py')

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
ipcMain.on('to-python', (_event: IpcMainEvent, arg: any) => {
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
ipcMain.handle('save-config', async (_event, config: AppConfig) => {
  const success = saveConfig(config)
  // 注意: 保存配置时不再自动注册快捷键
  // 快捷键只在用户点击"开始监听"时才注册
  return success
})

// 处理加载配置请求
ipcMain.handle('load-config', async () => {
  return loadConfig()
})

// 处理进入脚本运行模式 - 注册停止快捷键
ipcMain.handle('enter-script-mode', async (_event, stopKey: string) => {
  console.log('Entering script mode, registering stop hotkey:', stopKey)
  const success = registerStopHotkey(stopKey)
  return success
})

// 处理退出脚本运行模式 - 注销所有快捷键
ipcMain.handle('exit-script-mode', async () => {
  console.log('Exiting script mode, unregistering all hotkeys')
  unregisterAllHotkeys()
  return true
})

// 处理检查管理员权限请求
ipcMain.handle('check-admin-privileges', async () => {
  console.log('Checking admin privileges...')
  const hasAdmin = isAdmin()
  console.log('Admin privileges check result:', hasAdmin)
  return hasAdmin
})

// 处理获取项目配置请求
ipcMain.handle('get-project-config', async () => {
  console.log('Getting project config...')
  return projectConfig
})

// 处理请求管理员权限
ipcMain.handle('request-admin-privileges', async () => {
  console.log('Requesting admin privileges...')
  
  if (isAdmin()) {
    console.log('Already running with admin privileges')
    return true
  }

  try {
    // 根据操作系统选择不同的权限请求方式
    if (process.platform === 'win32') {
      // Windows: 显示友好的对话框，引导用户重启应用
      const options = {
        type: 'warning' as const,
        buttons: ['以管理员身份重启', '稍后手动设置', '取消'],
        defaultId: 0,
        title: '需要管理员权限',
        message: `${projectConfig.name} 需要管理员权限才能正常工作`,
        detail: '应用需要管理员权限来:\n' +
                '• 置顶游戏窗口\n' +
                '• 模拟鼠标和键盘操作\n' +
                '• 注册全局快捷键\n\n' +
                '推荐操作:\n' +
                '1. 点击"以管理员身份重启"立即获取权限\n' +
                '2. 或者右键桌面快捷方式 → 属性 → 兼容性 → 勾选"以管理员身份运行此程序"'
      }

      const result = dialog.showMessageBoxSync(win!, options)
      
      if (result === 0) {
        // 用户选择重启
        const exePath = process.execPath
        const args = process.argv.slice(1)
        
        const command = `Start-Process -FilePath "${exePath}" -ArgumentList "${args.join(' ')}" -Verb RunAs`
        exec(`powershell -Command "${command}"`, (error) => {
          if (error) {
            console.error('Failed to restart as admin:', error)
          }
          app.quit()
        })
        return true
      } else if (result === 1) {
        // 用户选择稍后手动设置
        console.log('User chose to manually set admin privileges later')
        return false
      } else {
        // 用户取消
        console.log('User cancelled admin privilege request')
        return false
      }
    } else if (process.platform === 'darwin') {
      // macOS: 显示说明对话框
      const options = {
        type: 'info' as const,
        buttons: ['我知道了', '取消'],
        defaultId: 0,
        title: '权限说明',
        message: `${projectConfig.name} 在 macOS 上的权限设置`,
        detail: `在 macOS 上，某些功能可能需要额外权限:\n\n` +
                `• 辅助功能权限 (用于窗口操作)\n` +
                `• 屏幕录制权限 (用于截图识别)\n\n` +
                `如果遇到权限问题，请到:\n` +
                `系统偏好设置 → 安全性与隐私 → 隐私\n` +
                `在相应选项中添加 ${projectConfig.name}`
      }

      const result = dialog.showMessageBoxSync(win!, options)
      return result === 0 // 用户点击"我知道了"返回true
    } else {
      // Linux: 显示说明对话框
      const options = {
        type: 'info' as const,
        buttons: ['我知道了', '取消'],
        defaultId: 0,
        title: '权限说明',
        message: `${projectConfig.name} 在 Linux 上的权限设置`,
        detail: '在 Linux 上，某些功能可能需要额外权限:\n\n' +
                '• X11 权限 (用于窗口操作)\n' +
                '• 输入设备权限 (用于模拟操作)\n\n' +
                '如果遇到权限问题，请使用 sudo 运行或\n' +
                '将用户添加到相应的用户组中'
      }

      const result = dialog.showMessageBoxSync(win!, options)
      return result === 0 // 用户点击"我知道了"返回true
    }
  } catch (error) {
    console.error('Failed to request admin privileges:', error)
    return false
  }
})

// 应用启动
app.whenReady().then(() => {
  console.log('App is ready, checking admin privileges...')
  
  // 检查管理员权限 - 只记录日志,不弹窗提示
  // 用户应该通过右键exe文件 -> 属性 -> 兼容性 -> 以管理员身份运行此程序
  // 或者使用"以管理员身份运行.bat"来启动
  if (!isAdmin()) {
    console.warn('⚠ Application is not running with administrator privileges')
    console.warn('⚠ Some features may not work properly (window activation, hotkeys, etc.)')
    console.warn('⚠ Please run as administrator for full functionality')
    // 不再弹窗,让程序继续运行
  } else {
    console.log('✓ Running with administrator privileges')
  }
  
  console.log('Creating window...')
  
  createWindow()
  startPythonEngine()

  // 注意: 不再在启动时自动注册快捷键
  // 快捷键只在用户点击"开始监听"时才注册

  app.on('activate', () => {
    // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// 应用退出时清理所有资源
app.on('will-quit', (event) => {
  console.log('Application will quit, performing cleanup...')
  
  // 1. 注销所有快捷键
  globalShortcut.unregisterAll()
  console.log('All hotkeys unregistered')
  
  // 2. 如果Python进程还在运行,发送取消置顶命令
  if (pyProc && pyProc.stdin) {
    try {
      const command = JSON.stringify({ action: 'deactivate_topmost' }) + '\n'
      pyProc.stdin.write(command)
      console.log('Sent deactivate_topmost command to Python')
      
      // 阻止立即退出,等待Python处理命令
      event.preventDefault()
      
      // 等待一小段时间后再退出
      setTimeout(() => {
        killPythonEngine()
        console.log('Python engine killed')
        app.exit(0)
      }, 200)
    } catch (error) {
      console.error('Failed to send cleanup command:', error)
      killPythonEngine()
    }
  } else {
    // Python进程已经停止,直接清理
    killPythonEngine()
  }
})
