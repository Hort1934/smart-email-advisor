import React, { useState, useEffect } from 'react'
import { Activity, Mail, Database, Wifi, Server } from 'lucide-react'
import axios from 'axios'

interface SystemStatusProps {}

interface StatusMetric {
  label: string
  value: string | number
  status: 'healthy' | 'warning' | 'error'
  icon: React.ReactNode
  description: string
}

export default function SystemStatus({}: SystemStatusProps) {
  const [metrics, setMetrics] = useState<StatusMetric[]>([
    {
      label: 'API Сервер',
      value: 'Перевірка...',
      status: 'warning',
      icon: <Server className="w-6 h-6" />,
      description: 'Статус backend API сервера'
    },
    {
      label: 'IMAP Підключення',
      value: 'Перевірка...',
      status: 'warning', 
      icon: <Mail className="w-6 h-6" />,
      description: 'Статус підключення до UKR.NET'
    },
    {
      label: 'База Даних',
      value: 'Перевірка...',
      status: 'warning',
      icon: <Database className="w-6 h-6" />,
      description: 'Статус PostgreSQL бази даних'
    },
    {
      label: 'Активність',
      value: 'Завантаження...',
      status: 'warning',
      icon: <Activity className="w-6 h-6" />,
      description: 'Останні оброблені листи'
    }
  ])

  useEffect(() => {
    checkSystemStatus()
    const interval = setInterval(checkSystemStatus, 30000) // Кожні 30 секунд
    return () => clearInterval(interval)
  }, [])

  const checkSystemStatus = async () => {
    try {
      // Перевірка API сервера
      const apiCheck = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/health`, {
        timeout: 5000
      }).catch(() => null)

      // Перевірка IMAP (через API endpoint)
      const imapCheck = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/imap-status`, {
        timeout: 10000
      }).catch(() => null)

      // Перевірка бази даних (опосередковано через API)
      const dbCheck = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/stats/stats`, {
        timeout: 5000
      }).catch(() => null)

      setMetrics(prev => prev.map(metric => {
        switch (metric.label) {
          case 'API Сервер':
            return {
              ...metric,
              value: apiCheck ? 'Online' : 'Offline',
              status: apiCheck ? 'healthy' : 'error'
            }
          case 'IMAP Підключення':
            return {
              ...metric,
              value: imapCheck ? 'Підключено' : 'Помилка',
              status: imapCheck ? 'healthy' : 'error'
            }
          case 'База Даних':
            return {
              ...metric,
              value: dbCheck ? 'Активна' : 'Помилка',
              status: dbCheck ? 'healthy' : 'error'
            }
          case 'Активність':
            const emailsCount = dbCheck?.data?.totalEmails || 0
            return {
              ...metric,
              value: `${emailsCount} листів`,
              status: emailsCount > 0 ? 'healthy' : 'warning'
            }
          default:
            return metric
        }
      }))

    } catch (error) {
      console.error('System status check failed:', error)
      
      setMetrics(prev => prev.map(metric => ({
        ...metric,
        value: 'Помилка',
        status: 'error' as const
      })))
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-success-600 bg-success-50 border-success-200'
      case 'warning': return 'text-warning-600 bg-warning-50 border-warning-200'
      case 'error': return 'text-danger-600 bg-danger-50 border-danger-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-success-500'
      case 'warning': return 'bg-warning-500'
      case 'error': return 'bg-danger-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <>
      {metrics.map((metric, index) => (
        <div key={index} className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${getStatusColor(metric.status)}`}>
              {metric.icon}
            </div>
            <div 
              className={`w-3 h-3 rounded-full ${getStatusIndicator(metric.status)}`}
              title={`Статус: ${metric.status}`}
            />
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 text-sm">{metric.label}</h3>
            <p className="text-lg font-bold text-gray-900 mt-1">{metric.value}</p>
            <p className="text-xs text-gray-600 mt-1" title={metric.description}>
              {metric.description}
            </p>
          </div>
        </div>
      ))}
    </>
  )
}