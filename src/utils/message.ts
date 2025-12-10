/**
 * ElMessage 封装工具
 * 
 * 这个文件封装了 Element Plus 的 ElMessage 组件，提供统一的消息提示接口
 * 
 * 使用方式：
 * import { message } from '@/utils/message'
 * 
 * message.success('操作成功')
 * message.error('操作失败')
 * message.warning('警告信息')
 * message.info('提示信息')
 */

import { ElMessage } from 'element-plus'
import type { MessageOptions } from 'element-plus'

/**
 * 消息类型
 */
type MessageType = 'success' | 'warning' | 'error' | 'info'

/**
 * 消息封装类
 */
class Message {
  /**
   * 显示成功消息
   * @param message 消息内容
   * @param options 可选配置项
   */
  success(message: string, options?: Partial<MessageOptions>) {
    return ElMessage.success({
      message,
      ...options
    })
  }

  /**
   * 显示警告消息
   * @param message 消息内容
   * @param options 可选配置项
   */
  warning(message: string, options?: Partial<MessageOptions>) {
    return ElMessage.warning({
      message,
      ...options
    })
  }

  /**
   * 显示错误消息
   * @param message 消息内容
   * @param options 可选配置项
   */
  error(message: string, options?: Partial<MessageOptions>) {
    return ElMessage.error({
      message,
      ...options
    })
  }

  /**
   * 显示信息消息
   * @param message 消息内容
   * @param options 可选配置项
   */
  info(message: string, options?: Partial<MessageOptions>) {
    return ElMessage.info({
      message,
      ...options
    })
  }

  /**
   * 通用消息方法
   * @param type 消息类型
   * @param message 消息内容
   * @param options 可选配置项
   */
  show(type: MessageType, message: string, options?: Partial<MessageOptions>) {
    return ElMessage({
      type,
      message,
      ...options
    })
  }
  /**
   * 关闭所有消息
   */
  close() {
    return ElMessage.closeAll()
  }
}

// 导出单例
export const message = new Message()

// 默认导出
export default message
