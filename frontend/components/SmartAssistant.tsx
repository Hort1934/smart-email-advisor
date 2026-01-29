import React, { useState, useEffect } from 'react'
import { Brain, MessageSquare, Settings, TrendingUp, Users, Clock, AlertTriangle, CheckCircle } from 'lucide-react'

interface SmartRecommendation {
  action_type: string
  priority: string
  title: string
  description: string
  suggested_response?: string
  confidence: number
  reasoning: string
  category: string
}

interface CommunicationAnalysis {
  tone: string
  sentiment: string
  emotions: string[]
  formality_level: string
  urgency_indicators: string[]
  relationship_context: string
  communication_style: string
}

interface SmartAnalysisResult {
  smart_recommendations: SmartRecommendation[]
  communication_analysis: CommunicationAnalysis
  personalized_insights: any
  confidence: number
}

interface SmartAssistantProps {
  emailId?: number
  onRecommendationExecute?: (recommendation: SmartRecommendation) => void
}

interface EmailItem {
  id: number
  sender: string
  recipient: string
  subject: string
  body: string
  priority: string
  is_spam: boolean
  created_at: string
  urgency_score: number
  communication_tone?: string
  emotions?: string[]
  practical_value?: number
  email_uid?: string
}

export default function SmartAssistant({ emailId, onRecommendationExecute }: SmartAssistantProps) {
  const [analysis, setAnalysis] = useState<SmartAnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedRecommendation, setSelectedRecommendation] = useState<SmartRecommendation | null>(null)
  const [showResponseGenerator, setShowResponseGenerator] = useState(false)
  const [generatedResponse, setGeneratedResponse] = useState<string>('')
  const [emails, setEmails] = useState<EmailItem[]>([])
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(emailId || null)
  const [loadingEmails, setLoadingEmails] = useState(true)

  useEffect(() => {
    loadEmails()
  }, [])

  useEffect(() => {
    if (selectedEmailId) {
      analyzeEmail()
    }
  }, [selectedEmailId])

  const loadEmails = async () => {
    setLoadingEmails(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/emails?limit=20`)
      if (response.ok) {
        const data = await response.json()
        setEmails(data.emails || [])
        if ((data.emails || []).length > 0 && !selectedEmailId) {
          setSelectedEmailId(data.emails[0].id)
        }
      }
    } catch (error) {
      console.error('Error loading emails:', error)
    } finally {
      setLoadingEmails(false)
    }
  }

  const analyzeEmail = async () => {
    if (!selectedEmailId) return
    
    setLoading(true)
    try {
      // Знайти email_uid для вибраного листа
      const selectedEmail = emails.find(email => email.id === selectedEmailId)
      if (!selectedEmail || !selectedEmail.email_uid) {
        console.error('Email UID not found for selected email')
        return
      }
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/analyze-smart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_uid: selectedEmail.email_uid,
          analyze_tone: true,
          generate_response: false
        })
      })

      if (response.ok) {
        const result = await response.json()
        setAnalysis(result)
      }
    } catch (error) {
      console.error('Error analyzing email:', error)
    } finally {
      setLoading(false)
    }
  }

  const executeRecommendation = async (recommendation: SmartRecommendation) => {
    setSelectedRecommendation(recommendation)
    
    try {
      // Виконуємо дії залежно від типу рекомендації
      switch (recommendation.action_type) {
        case 'reply':
        case 'reply_diplomatic':
          setShowResponseGenerator(true)
          await generateResponse(recommendation)
          break
          
        case 'archive':
          // Показуємо підтвердження архівування
          if (confirm('Ви впевнені що хочете архівувати цей лист?')) {
            await archiveEmail(selectedEmailId!)
            alert('Лист успішно архівовано!')
          }
          break
          
        case 'create_task':
          // Показуємо діалог створення задачі
          const taskTitle = prompt('Введіть назву задачі:', recommendation.title)
          if (taskTitle) {
            await createTask({
              title: taskTitle,
              description: recommendation.description,
              emailId: selectedEmailId!,
              priority: recommendation.priority
            })
            alert('Задачу створено!')
          }
          break
          
        case 'schedule':
          alert('Функція планування буде доступна незабаром')
          break
          
        default:
          alert('Дію виконано!')
      }
      
      // Надсилаємо позитивний фідбек
      await submitFeedback(recommendation, true, 5)
    } catch (error) {
      console.error('Error executing recommendation:', error)
      alert('Помилка при виконанні дії')
    }
    
    onRecommendationExecute?.(recommendation)
  }

  const generateResponse = async (recommendation: SmartRecommendation) => {
    try {
      const responseStyle = recommendation.action_type === 'reply_diplomatic' ? 'diplomatic' : 'professional'
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/generate-response`)
      url.searchParams.append('email_id', selectedEmailId!.toString())
      url.searchParams.append('response_style', responseStyle)
      
      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        const result = await response.json()
        setGeneratedResponse(result.suggested_response)
      } else {
        console.error('Failed to generate response:', response.status)
        setGeneratedResponse('Помилка генерації відповіді. Спробуйте пізніше.')
      }
    } catch (error) {
      console.error('Error generating response:', error)
      setGeneratedResponse('Помилка генерації відповіді. Спробуйте пізніше.')
    }
  }

  const submitFeedback = async (recommendation: SmartRecommendation, helpful: boolean, satisfaction: number) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/learn-from-feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_id: emailId,
          user_action: recommendation.action_type,
          was_recommendation_helpful: helpful,
          user_satisfaction: satisfaction
        })
      })
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  const archiveEmail = async (emailId: number) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/emails/${emailId}/archive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to archive email')
      }
    } catch (error) {
      console.error('Error archiving email:', error)
      throw error
    }
  }

  const createTask = async (task: {title: string, description: string, emailId: number, priority: string}) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/create-task`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(task)
      })
      
      if (!response.ok) {
        throw new Error('Failed to create task')
      }
    } catch (error) {
      console.error('Error creating task:', error)
      throw error
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'reply':
      case 'reply_diplomatic': return <MessageSquare className="w-4 h-4" />
      case 'archive': return <CheckCircle className="w-4 h-4" />
      case 'schedule': return <Clock className="w-4 h-4" />
      case 'meeting': return <Users className="w-4 h-4" />
      default: return <Brain className="w-4 h-4" />
    }
  }

  const getToneEmoji = (tone: string) => {
    switch (tone) {
      case 'aggressive': return '⚡'
      case 'friendly': return '😊'
      case 'professional': return '💼'
      case 'urgent': return '🚨'
      case 'neutral': return '📝'
      default: return '📧'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <Brain className="w-6 h-6 text-blue-600 animate-pulse" />
          <span className="text-gray-600">AI помічник аналізує лист...</span>
        </div>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <Brain className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>Оберіть лист для отримання розумних рекомендацій</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Communication Analysis */}
      {analysis.communication_analysis && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            Аналіз комунікації
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Тон:</span>
                <span className="flex items-center space-x-1">
                  <span>{getToneEmoji(analysis.communication_analysis.tone)}</span>
                  <span className="text-sm font-medium capitalize">{analysis.communication_analysis.tone}</span>
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Настрій:</span>
                <span className="text-sm font-medium capitalize">{analysis.communication_analysis.sentiment}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Контекст:</span>
                <span className="text-sm font-medium capitalize">{analysis.communication_analysis.relationship_context}</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-600">Емоції:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {analysis.communication_analysis.emotions.map((emotion, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      {emotion}
                    </span>
                  ))}
                </div>
              </div>
              
              {analysis.communication_analysis.urgency_indicators.length > 0 && (
                <div>
                  <span className="text-sm text-gray-600 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1 text-amber-500" />
                    Індикатори терміновості:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {analysis.communication_analysis.urgency_indicators.map((indicator, index) => (
                      <span key={index} className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full">
                        {indicator}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Smart Recommendations */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Brain className="w-5 h-5 mr-2 text-blue-600" />
          Розумні рекомендації
          <span className="ml-2 text-sm text-gray-500">
            ({analysis.smart_recommendations.length})
          </span>
        </h3>
        
        <div className="space-y-3">
          {analysis.smart_recommendations.map((recommendation, index) => (
            <div 
              key={index} 
              className={`border rounded-lg p-4 transition-colors hover:bg-gray-50 ${getPriorityColor(recommendation.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    {getActionIcon(recommendation.action_type)}
                    <h4 className="font-medium">{recommendation.title}</h4>
                    <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(recommendation.priority)}`}>
                      {recommendation.priority}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">{recommendation.description}</p>
                  
                  {recommendation.reasoning && (
                    <p className="text-xs text-gray-500 italic">
                      Обґрунтування: {recommendation.reasoning}
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between mt-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        Впевненість: {Math.round(recommendation.confidence * 100)}%
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500 capitalize">
                        {recommendation.category}
                      </span>
                    </div>
                    
                    <button
                      onClick={() => executeRecommendation(recommendation)}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Виконати
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {analysis.smart_recommendations.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <Brain className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>Немає специфічних рекомендацій для цього листа</p>
          </div>
        )}
      </div>

      {/* Response Generator Modal */}
      {showResponseGenerator && generatedResponse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
                Згенерована відповідь
              </h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Запропонований текст:
                </label>
                <textarea
                  value={generatedResponse}
                  onChange={(e) => setGeneratedResponse(e.target.value)}
                  className="w-full h-32 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Згенерований текст відповіді..."
                />
              </div>
              
              <div className="flex justify-between items-center">
                <div className="space-x-2">
                  <button
                    onClick={() => submitFeedback(selectedRecommendation!, true, 5)}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    👍 Корисно
                  </button>
                  <button
                    onClick={() => submitFeedback(selectedRecommendation!, false, 2)}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    👎 Не корисно
                  </button>
                </div>
                
                <div className="space-x-2">
                  <button
                    onClick={() => setShowResponseGenerator(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                  >
                    Закрити
                  </button>
                  <button
                    onClick={() => {
                      // Copy to clipboard
                      navigator.clipboard.writeText(generatedResponse)
                      setShowResponseGenerator(false)
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Копіювати
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}