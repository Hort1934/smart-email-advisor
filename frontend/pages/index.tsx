import React, { useState, useEffect } from 'react'
import { Mail, Activity, Database, Brain, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import EmailProcessingDashboard from '../components/EmailProcessingDashboard'
import SpamAnalysisStats from '../components/SpamAnalysisStats'
import ProcessingLogs from '../components/ProcessingLogs'
import SystemStatus from '../components/SystemStatus'

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'warning' | 'error'>('healthy')

  // Перевірка статусу системи при завантаженні
  useEffect(() => {
    checkSystemHealth()
    const interval = setInterval(checkSystemHealth, 30000) // Кожні 30 секунд
    return () => clearInterval(interval)
  }, [])

  const checkSystemHealth = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      if (response.ok) {
        setSystemHealth('healthy')
      } else {
        setSystemHealth('warning')
      }
    } catch (error) {
      setSystemHealth('error')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-success-600'
      case 'warning': return 'text-warning-600'
      case 'error': return 'text-danger-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />
      case 'warning': return <AlertCircle className="w-5 h-5" />
      case 'error': return <AlertCircle className="w-5 h-5" />
      default: return <Clock className="w-5 h-5" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Mail className="w-8 h-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Smart Email Advisor</h1>
                <p className="text-sm text-gray-600">Dashboard обробки spam листів</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Статус системи */}
              <div className={`flex items-center space-x-2 ${getStatusColor(systemHealth)}`}>
                {getStatusIcon(systemHealth)}
                <span className="text-sm font-medium capitalize">{systemHealth}</span>
              </div>
              
              {/* Кнопка оновлення */}
              <button
                onClick={checkSystemHealth}
                className="btn-secondary flex items-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Оновити</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* System Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <SystemStatus />
          </div>

          {/* Main Dashboard */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Processing Dashboard - займає 2 колонки */}
            <div className="lg:col-span-2">
              <EmailProcessingDashboard 
                isProcessing={isProcessing}
                setIsProcessing={setIsProcessing}
              />
            </div>
            
            {/* Statistics Panel */}
            <div className="space-y-6">
              <SpamAnalysisStats />
            </div>
          </div>

          {/* Processing Logs */}
          <div className="w-full">
            <ProcessingLogs />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              © 2026 Smart Email Advisor. Powered by AI.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Activity className="w-4 h-4" />
                <span>API: {process.env.NEXT_PUBLIC_API_URL}</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}