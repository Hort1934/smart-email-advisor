import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, Shield, Mail, AlertTriangle } from 'lucide-react'
import axios from 'axios'

interface Stats {
  totalEmails: number
  analyzedToday: number
  threatLevels: {
    high: number
    medium: number
    low: number
  }
  categories: Array<{
    name: string
    count: number
  }>
}

export default function SpamAnalysisStats() {
  const [stats, setStats] = useState<Stats>({
    totalEmails: 0,
    analyzedToday: 0,
    threatLevels: { high: 0, medium: 0, low: 0 },
    categories: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 60000) // Оновлюємо кожну хвилину
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/stats/stats`)
      
      if (response.data) {
        setStats(response.data)
      } else {
        // Fallback до мок даних
        const mockStats: Stats = {
          totalEmails: 0,
          analyzedToday: 0,
          threatLevels: { high: 0, medium: 0, low: 0 },
          categories: [
            { name: 'Фішинг', count: 0 },
            { name: 'Реклама', count: 0 },
            { name: 'Шахрайство', count: 0 },
            { name: 'Малвар', count: 0 },
            { name: 'Інше', count: 0 }
          ]
        }
        setStats(mockStats)
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching stats:', error)
      
      // Використовуємо мок дані при помилці
      const fallbackStats: Stats = {
        totalEmails: 0,
        analyzedToday: 0,
        threatLevels: { high: 0, medium: 0, low: 0 },
        categories: [
          { name: 'Фішинг', count: 0 },
          { name: 'Реклама', count: 0 },
          { name: 'Шахрайство', count: 0 },
          { name: 'Малвар', count: 0 },
          { name: 'Інше', count: 0 }
        ]
      }
      setStats(fallbackStats)
      setLoading(false)
    }
  }

  const threatLevelData = [
    { name: 'Високий', value: stats.threatLevels.high, color: '#DC2626' },
    { name: 'Середній', value: stats.threatLevels.medium, color: '#D97706' },
    { name: 'Низький', value: stats.threatLevels.low, color: '#059669' }
  ]

  const categoryData = stats.categories.map(cat => ({
    name: cat.name,
    emails: cat.count
  }))

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-300 rounded"></div>
            <div className="h-3 bg-gray-300 rounded w-3/4"></div>
            <div className="h-3 bg-gray-300 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-primary-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary-600 font-medium">Всього листів</p>
                <p className="text-2xl font-bold text-primary-900">{stats.totalEmails}</p>
              </div>
              <Mail className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          
          <div className="bg-success-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-success-600 font-medium">Сьогодні</p>
                <p className="text-2xl font-bold text-success-900">{stats.analyzedToday}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-success-600" />
            </div>
          </div>
        </div>

        {/* Threat Levels Chart */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Рівні загроз</h4>
          <div style={{ width: '100%', height: 200 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={threatLevelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                >
                  {threatLevelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any) => [`${value} листів`, 'Кількість']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex justify-center space-x-4 mt-3">
            {threatLevelData.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-gray-600">{item.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Threat Summary */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-danger-100 rounded-lg mx-auto mb-2">
              <AlertTriangle className="w-5 h-5 text-danger-600" />
            </div>
            <p className="text-xs text-gray-600">Високий</p>
            <p className="text-lg font-bold text-danger-900">{stats.threatLevels.high}</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-warning-100 rounded-lg mx-auto mb-2">
              <AlertTriangle className="w-5 h-5 text-warning-600" />
            </div>
            <p className="text-xs text-gray-600">Середній</p>
            <p className="text-lg font-bold text-warning-900">{stats.threatLevels.medium}</p>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-success-100 rounded-lg mx-auto mb-2">
              <Shield className="w-5 h-5 text-success-600" />
            </div>
            <p className="text-xs text-gray-600">Низький</p>
            <p className="text-lg font-bold text-success-900">{stats.threatLevels.low}</p>
          </div>
        </div>
      </div>

      {/* Categories Chart */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Категорії spam</h4>
        <div style={{ width: '100%', height: 250 }}>
          <ResponsiveContainer>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: any) => [`${value} листів`, 'Кількість']}
                labelStyle={{ color: '#374151' }}
              />
              <Bar 
                dataKey="emails" 
                fill="#3B82F6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}