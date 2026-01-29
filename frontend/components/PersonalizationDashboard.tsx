import React, { useState, useEffect } from 'react'
import { Settings, User, Clock, MessageCircle, Brain, Save, TrendingUp } from 'lucide-react'

interface PersonalizationSettings {
  communication_style: string
  response_tone: string
  priority_keywords: string[]
  work_hours: {
    start: string
    end: string
  }
  notification_preferences: Record<string, any>
}

interface CommunicationInsights {
  period_days: number
  tone_distribution: Record<string, number>
  relationship_contexts: Record<string, { count: number; avg_urgency: number }>
  value_patterns: Record<string, { count: number; attention_rate: number }>
  insights: string[]
}

export default function PersonalizationDashboard() {
  const [settings, setSettings] = useState<PersonalizationSettings>({
    communication_style: 'professional',
    response_tone: 'balanced', 
    priority_keywords: [],
    work_hours: { start: '09:00', end: '18:00' },
    notification_preferences: {}
  })
  
  const [insights, setInsights] = useState<CommunicationInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [newKeyword, setNewKeyword] = useState('')

  useEffect(() => {
    loadSettings()
    loadInsights()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/personalization/settings`)
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
      }
    } catch (error) {
      console.error('Error loading settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadInsights = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/insights/communication-patterns?days=30`)
      if (response.ok) {
        const data = await response.json()
        setInsights(data)
      }
    } catch (error) {
      console.error('Error loading insights:', error)
    }
  }

  const saveSettings = async () => {
    setSaving(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/smart/personalization/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      })
      
      if (response.ok) {
        alert('Налаштування збережено!')
      }
    } catch (error) {
      console.error('Error saving settings:', error)
      alert('Помилка збереження налаштувань')
    } finally {
      setSaving(false)
    }
  }

  const addKeyword = () => {
    if (newKeyword.trim() && !settings.priority_keywords.includes(newKeyword.trim())) {
      setSettings({
        ...settings,
        priority_keywords: [...settings.priority_keywords, newKeyword.trim()]
      })
      setNewKeyword('')
    }
  }

  const removeKeyword = (keyword: string) => {
    setSettings({
      ...settings,
      priority_keywords: settings.priority_keywords.filter(k => k !== keyword)
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <Brain className="w-6 h-6 mr-3 text-blue-600" />
          Персональний AI Помічник
        </h2>
        <p className="text-gray-600">
          Налаштуйте вашого персонального помічника для роботи з email. 
          Система навчається на ваших діях та покращує рекомендації.
        </p>
      </div>

      {/* Communication Style Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <MessageCircle className="w-5 h-5 mr-2 text-blue-600" />
          Стиль комунікації
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Основний стиль
            </label>
            <select
              value={settings.communication_style}
              onChange={(e) => setSettings({...settings, communication_style: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="professional">Професійний</option>
              <option value="diplomatic">Дипломатичний</option>
              <option value="direct">Прямий</option>
              <option value="friendly">Дружний</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тон відповідей
            </label>
            <select
              value={settings.response_tone}
              onChange={(e) => setSettings({...settings, response_tone: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="formal">Формальний</option>
              <option value="balanced">Збалансований</option>
              <option value="casual">Неформальний</option>
            </select>
          </div>
        </div>
      </div>

      {/* Work Schedule */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2 text-blue-600" />
          Робочий графік
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Початок роботи
            </label>
            <input
              type="time"
              value={settings.work_hours.start}
              onChange={(e) => setSettings({
                ...settings, 
                work_hours: {...settings.work_hours, start: e.target.value}
              })}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Кінець роботи
            </label>
            <input
              type="time"
              value={settings.work_hours.end}
              onChange={(e) => setSettings({
                ...settings, 
                work_hours: {...settings.work_hours, end: e.target.value}
              })}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Priority Keywords */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2 text-blue-600" />
          Пріоритетні ключові слова
        </h3>
        
        <div className="mb-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
              placeholder="Додати ключове слово..."
              className="flex-1 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              onClick={addKeyword}
              className="px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Додати
            </button>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {settings.priority_keywords.map((keyword, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
            >
              {keyword}
              <button
                onClick={() => removeKeyword(keyword)}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        
        {settings.priority_keywords.length === 0 && (
          <p className="text-gray-500 text-sm mt-2">
            Додайте ключові слова, які допоможуть системі визначати пріоритетність листів
          </p>
        )}
      </div>

      {/* Communication Insights */}
      {insights && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            Аналітика комунікації (останні {insights.period_days} днів)
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tone Distribution */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Розподіл тонів</h4>
              <div className="space-y-2">
                {Object.entries(insights.tone_distribution).map(([tone, count]) => (
                  <div key={tone} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{tone}</span>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Relationship Contexts */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Контексти стосунків</h4>
              <div className="space-y-2">
                {Object.entries(insights.relationship_contexts).map(([context, data]) => (
                  <div key={context} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{context}</span>
                    <span className="text-sm font-medium">{data.count}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Value Patterns */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Патерни цінності</h4>
              <div className="space-y-2">
                {Object.entries(insights.value_patterns).map(([pattern, data]) => (
                  <div key={pattern} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{pattern}</span>
                    <span className="text-sm font-medium">{data.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Insights */}
          {insights.insights.length > 0 && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Персональні інсайти:</h4>
              <ul className="space-y-1">
                {insights.insights.map((insight, index) => (
                  <li key={index} className="text-sm text-blue-800">• {insight}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveSettings}
          disabled={saving}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Збереження...' : 'Зберегти налаштування'}</span>
        </button>
      </div>
    </div>
  )
}