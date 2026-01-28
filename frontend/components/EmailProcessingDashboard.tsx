import React, { useState, useEffect } from 'react'
import { Play, Pause, Mail, Brain, Database, AlertTriangle } from 'lucide-react'
import axios from 'axios'

interface EmailProcessingDashboardProps {
  isProcessing: boolean
  setIsProcessing: (processing: boolean) => void
}

interface ProcessingStep {
  id: string
  name: string
  status: 'waiting' | 'processing' | 'completed' | 'error'
  description: string
  icon: React.ReactNode
  duration?: number
}

interface SpamEmail {
  id: string
  subject: string
  sender: string
  received_date: string
  priority?: string
  threat_level?: string
  analysis_summary?: string
}

export default function EmailProcessingDashboard({ isProcessing, setIsProcessing }: EmailProcessingDashboardProps) {
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    {
      id: 'fetch',
      name: 'Отримання spam листів',
      status: 'waiting',
      description: 'Підключення до UKR.NET IMAP та завантаження нових spam листів',
      icon: <Mail className="w-5 h-5" />
    },
    {
      id: 'analyze',
      name: 'AI Аналіз',
      status: 'waiting',
      description: 'Обробка листів за допомогою штучного інтелекту',
      icon: <Brain className="w-5 h-5" />
    },
    {
      id: 'store',
      name: 'Збереження',
      status: 'waiting',
      description: 'Збереження результатів аналізу в базу даних',
      icon: <Database className="w-5 h-5" />
    }
  ])

  const [processedEmails, setProcessedEmails] = useState<SpamEmail[]>([])
  const [currentStep, setCurrentStep] = useState<number>(0)
  const [processingError, setProcessingError] = useState<string | null>(null)

  const startProcessing = async () => {
    if (isProcessing) return

    setIsProcessing(true)
    setProcessingError(null)
    setCurrentStep(0)
    
    // Скидаємо статуси
    setProcessingSteps(steps => steps.map(step => ({ ...step, status: 'waiting' as const })))

    try {
      // Крок 1: Отримання spam листів
      setProcessingSteps(steps => 
        steps.map((step, index) => ({
          ...step,
          status: index === 0 ? 'processing' : 'waiting'
        }))
      )
      setCurrentStep(0)

      const spamResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/emails/spam`)
      
      setProcessingSteps(steps => 
        steps.map((step, index) => ({
          ...step,
          status: index === 0 ? 'completed' : (index === 1 ? 'processing' : 'waiting')
        }))
      )
      setCurrentStep(1)

      // Крок 2: AI Аналіз
      const analysisResponse = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/emails/analyze-from-spam`)
      
      setProcessingSteps(steps => 
        steps.map((step, index) => ({
          ...step,
          status: index <= 1 ? 'completed' : (index === 2 ? 'processing' : 'waiting')
        }))
      )
      setCurrentStep(2)

      // Імітуємо збереження (уже відбувається автоматично в API)
      await new Promise(resolve => setTimeout(resolve, 1000))

      setProcessingSteps(steps => 
        steps.map(step => ({ ...step, status: 'completed' as const }))
      )

      // Оновлюємо список оброблених листів - отримуємо з нового endpoint
      try {
        const recentEmailsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/stats/recent-emails?limit=5`)
        if (recentEmailsResponse.data) {
          setProcessedEmails(recentEmailsResponse.data)
        } else if (analysisResponse.data.analyzed_emails) {
          setProcessedEmails(analysisResponse.data.analyzed_emails.slice(0, 5))
        }
      } catch (emailError) {
        console.warn('Could not fetch recent emails:', emailError)
        // Fallback до відповіді аналізу
        if (analysisResponse.data.analyzed_emails) {
          setProcessedEmails(analysisResponse.data.analyzed_emails.slice(0, 5))
        }
      }

    } catch (error: any) {
      console.error('Processing error:', error)
      setProcessingError(error.response?.data?.detail || 'Помилка обробки листів')
      
      // Позначаємо поточний крок як помилковий
      setProcessingSteps(steps => 
        steps.map((step, index) => ({
          ...step,
          status: index < currentStep ? 'completed' : (index === currentStep ? 'error' : 'waiting')
        }))
      )
    } finally {
      setIsProcessing(false)
    }
  }

  const stopProcessing = () => {
    setIsProcessing(false)
    setProcessingSteps(steps => 
      steps.map(step => ({
        ...step,
        status: step.status === 'processing' ? 'waiting' : step.status
      }))
    )
  }

  const getStepStatusClass = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-success-100 text-success-800 border-success-200'
      case 'processing': return 'bg-primary-100 text-primary-800 border-primary-200 animate-pulse'
      case 'error': return 'bg-danger-100 text-danger-800 border-danger-200'
      default: return 'bg-gray-100 text-gray-600 border-gray-200'
    }
  }

  const getStepIconClass = (status: string) => {
    switch (status) {
      case 'completed': return 'text-success-600'
      case 'processing': return 'text-primary-600'
      case 'error': return 'text-danger-600'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Обробка Spam Листів</h2>
        
        <button
          onClick={isProcessing ? stopProcessing : startProcessing}
          disabled={false}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            isProcessing
              ? 'bg-danger-600 hover:bg-danger-700 text-white'
              : 'bg-primary-600 hover:bg-primary-700 text-white'
          }`}
        >
          {isProcessing ? (
            <>
              <Pause className="w-4 h-4" />
              <span>Зупинити</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Запустити обробку</span>
            </>
          )}
        </button>
      </div>

      {/* Processing Steps */}
      <div className="space-y-4 mb-8">
        {processingSteps.map((step, index) => (
          <div
            key={step.id}
            className={`p-4 rounded-lg border-2 transition-all ${getStepStatusClass(step.status)}`}
          >
            <div className="flex items-start space-x-3">
              <div className={`mt-1 ${getStepIconClass(step.status)}`}>
                {step.icon}
              </div>
              <div className="flex-1">
                <h3 className="font-medium">{step.name}</h3>
                <p className="text-sm opacity-80 mt-1">{step.description}</p>
                {step.status === 'processing' && (
                  <div className="mt-2">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
                      <span className="text-sm">Обробляємо...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Error Display */}
      {processingError && (
        <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-danger-600" />
            <p className="text-danger-800 font-medium">Помилка обробки</p>
          </div>
          <p className="text-danger-700 text-sm mt-1">{processingError}</p>
        </div>
      )}

      {/* Recently Processed Emails */}
      {processedEmails.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Останні оброблені листи</h3>
          <div className="space-y-3">
            {processedEmails.map((email, index) => (
              <div key={email.id || index} className="p-3 bg-gray-50 rounded-lg border">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 truncate">{email.subject}</h4>
                    <p className="text-sm text-gray-600">Від: {email.sender}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(email.received_date).toLocaleString('uk-UA')}
                    </p>
                  </div>
                  <div className="ml-4 flex flex-col items-end space-y-1">
                    {email.threat_level && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        email.threat_level === 'high' ? 'bg-danger-100 text-danger-800' :
                        email.threat_level === 'medium' ? 'bg-warning-100 text-warning-800' :
                        'bg-success-100 text-success-800'
                      }`}>
                        {email.threat_level === 'high' ? 'Високий' :
                         email.threat_level === 'medium' ? 'Середній' : 'Низький'}
                      </span>
                    )}
                    {email.priority && (
                      <span className="status-badge-info">
                        {email.priority}
                      </span>
                    )}
                  </div>
                </div>
                {email.analysis_summary && (
                  <p className="text-sm text-gray-700 mt-2 line-clamp-2">{email.analysis_summary}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}