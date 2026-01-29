import React, { useState, useEffect } from 'react'
import { Mail, AlertTriangle, CheckCircle, Clock, User } from 'lucide-react'

interface Email {
  id: number
  sender: string
  recipient: string
  subject: string
  body: string
  priority: 'high' | 'medium' | 'low'
  is_spam: boolean
  created_at: string
  urgency_score: number
  communication_tone?: string
  emotions?: string[]
  practical_value?: number
  email_uid?: string
}

interface EmailListProps {
  onEmailSelect: (emailId: number) => void
  selectedEmailId: number | null
}

const EmailList: React.FC<EmailListProps> = ({ onEmailSelect, selectedEmailId }) => {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadEmails()
  }, [])

  const loadEmails = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/emails?limit=20`)
      
      if (!response.ok) {
        throw new Error('Не вдалося завантажити листи')
      }
      
      const data = await response.json()
      setEmails(data.emails || [])
    } catch (error) {
      console.error('Error loading emails:', error)
      setError(error instanceof Error ? error.message : 'Помилка завантаження')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-600" />
      case 'medium':
        return <Clock className="w-4 h-4 text-yellow-600" />
      case 'low':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      default:
        return <Mail className="w-4 h-4 text-gray-600" />
    }
  }

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high': return 'Високий'
      case 'medium': return 'Середній'
      case 'low': return 'Низький'
      default: return 'Невідомий'
    }
  }

  const getToneEmoji = (tone?: string) => {
    if (!tone) return '📧'
    
    switch (tone) {
      case 'aggressive': return '⚡'
      case 'friendly': return '😊'
      case 'professional': return '💼'
      case 'urgent': return '🚨'
      case 'neutral': return '📝'
      default: return '📧'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('uk-UA', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <h3 className="text-lg font-semibold mb-4">Завантаження листів...</h3>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{error}</p>
          <button 
            onClick={loadEmails}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Спробувати ще раз
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold flex items-center">
          <Mail className="w-5 h-5 mr-2 text-blue-600" />
          Оберіть лист для аналізу
          <span className="ml-2 text-sm text-gray-500">({emails.length})</span>
        </h3>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        {emails.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <Mail className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>Листи не знайдено</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {emails.map((email) => (
              <div
                key={email.id}
                onClick={() => onEmailSelect(email.id)}
                className={`p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                  selectedEmailId === email.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      {getPriorityIcon(email.priority)}
                      <span className="text-xs font-medium text-gray-500">
                        {getPriorityText(email.priority)}
                      </span>
                      {email.communication_tone && (
                        <span className="text-xs">
                          {getToneEmoji(email.communication_tone)}
                        </span>
                      )}
                      {email.is_spam && (
                        <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                          Спам
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 mb-1">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {email.sender}
                      </span>
                    </div>
                    
                    <h4 className="text-sm font-medium text-gray-900 truncate mb-1">
                      {email.subject}
                    </h4>
                    
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {email.body.substring(0, 100)}...
                    </p>
                    
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-500">
                        {formatDate(email.created_at)}
                      </span>
                      
                      <div className="flex items-center space-x-2">
                        {email.urgency_score > 0.7 && (
                          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                            Терміново
                          </span>
                        )}
                        {email.practical_value && email.practical_value > 0.8 && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            Важливо
                          </span>
                        )}
                      </div>
                    </div>
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

export default EmailList