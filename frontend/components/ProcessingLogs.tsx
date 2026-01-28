import React, { useState, useEffect } from 'react'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import axios from 'axios'

interface ProcessingLog {
  id: string
  timestamp: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
  details?: string
  emailSubject?: string
}

export default function ProcessingLogs() {
  const [logs, setLogs] = useState<ProcessingLog[]>([])
  const [filter, setFilter] = useState<'all' | 'info' | 'success' | 'warning' | 'error'>('all')

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 30000) // Оновлюємо кожні 30 секунд
    return () => clearInterval(interval)
  }, [filter])

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/logs/processing-logs`, {
        params: {
          limit: 20,
          log_type: filter === 'all' ? undefined : filter
        }
      })
      
      if (response.data) {
        setLogs(response.data)
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
      
      // Fallback до мок логів при помилці
      const fallbackLogs: ProcessingLog[] = [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          type: 'info',
          message: 'Неможливо завантажити логи',
          details: 'Помилка підключення до API'
        }
      ]
      setLogs(fallbackLogs)
    }
  }

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.type === filter)

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-success-600" />
      case 'error': return <XCircle className="w-4 h-4 text-danger-600" />
      case 'warning': return <AlertCircle className="w-4 h-4 text-warning-600" />
      default: return <FileText className="w-4 h-4 text-primary-600" />
    }
  }

  const getLogBgColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-success-50 border-l-success-500'
      case 'error': return 'bg-danger-50 border-l-danger-500'
      case 'warning': return 'bg-warning-50 border-l-warning-500'
      default: return 'bg-primary-50 border-l-primary-500'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Щойно'
    if (diffMins < 60) return `${diffMins} хв тому`
    
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours} год тому`
    
    return date.toLocaleDateString('uk-UA') + ' ' + date.toLocaleTimeString('uk-UA', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const getFilterCount = (type: string) => {
    return logs.filter(log => log.type === type).length
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      <div className="px-6 py-4 border-b">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Логи Обробки</h3>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Оновлення в реальному часі</span>
          </div>
        </div>
        
        {/* Фільтри */}
        <div className="flex flex-wrap gap-2 mt-4">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === 'all' 
                ? 'bg-gray-900 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Всі ({logs.length})
          </button>
          
          <button
            onClick={() => setFilter('success')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === 'success' 
                ? 'bg-success-600 text-white' 
                : 'bg-success-100 text-success-700 hover:bg-success-200'
            }`}
          >
            Успіх ({getFilterCount('success')})
          </button>
          
          <button
            onClick={() => setFilter('warning')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === 'warning' 
                ? 'bg-warning-600 text-white' 
                : 'bg-warning-100 text-warning-700 hover:bg-warning-200'
            }`}
          >
            Попередження ({getFilterCount('warning')})
          </button>
          
          <button
            onClick={() => setFilter('error')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === 'error' 
                ? 'bg-danger-600 text-white' 
                : 'bg-danger-100 text-danger-700 hover:bg-danger-200'
            }`}
          >
            Помилки ({getFilterCount('error')})
          </button>
          
          <button
            onClick={() => setFilter('info')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === 'info' 
                ? 'bg-primary-600 text-white' 
                : 'bg-primary-100 text-primary-700 hover:bg-primary-200'
            }`}
          >
            Інфо ({getFilterCount('info')})
          </button>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Немає логів для відображення</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLogs.map((log) => (
              <div 
                key={log.id} 
                className={`p-4 border-l-4 ${getLogBgColor(log.type)}`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getLogIcon(log.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900">{log.message}</p>
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        {formatTime(log.timestamp)}
                      </span>
                    </div>
                    
                    {log.details && (
                      <p className="text-sm text-gray-700 mt-1">{log.details}</p>
                    )}
                    
                    {log.emailSubject && (
                      <div className="mt-2 p-2 bg-white bg-opacity-70 rounded border">
                        <p className="text-xs text-gray-600 font-medium">Тема листа:</p>
                        <p className="text-sm text-gray-800 italic">{log.emailSubject}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}