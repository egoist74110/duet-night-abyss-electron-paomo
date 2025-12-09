import { app, BrowserWindow } from 'electron'
import { join } from 'path'

// 屏蔽安全警告
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true'

let win: BrowserWindow | null = null

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

// 应用启动
app.whenReady().then(() => {
  console.log('App is ready, creating window...')
  createWindow()
  startPythonEngine()

  app.on('activate', () => {
    // 在 macOS 上,当点击 dock 图标且没有其他窗口打开时,重新创建窗口
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})
