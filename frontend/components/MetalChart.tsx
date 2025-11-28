'use client';

import { useEffect, useState } from 'react';
import { metalsAPI, type HistoricalDataPoint } from '@/lib/api';

interface MetalChartProps {
  symbol: string;
  days: number;
}

export default function MetalChart({ symbol, days }: MetalChartProps) {
  const [data, setData] = useState<HistoricalDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistoricalData();
  }, [symbol, days]);

  const fetchHistoricalData = async () => {
    try {
      setLoading(true);
      const response = await metalsAPI.getHistorical(symbol, days);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch historical data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading chart data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">No data available</div>
      </div>
    );
  }

  // Calculate chart dimensions and scaling
  const prices = data.map(d => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1; // 10% padding

  const chartHeight = 300;
  const chartWidth = 800;
  const pointCount = data.length;

  // Generate SVG path for the price line
  const points = data.map((point, index) => {
    const x = (index / (pointCount - 1)) * chartWidth;
    const y = chartHeight - ((point.close - minPrice + padding) / (priceRange + 2 * padding)) * chartHeight;
    return `${x},${y}`;
  });

  const pathData = `M ${points.join(' L ')}`;

  // Generate area fill path
  const areaPoints = [
    `M 0,${chartHeight}`,
    `L ${points[0]}`,
    ...points.slice(1).map(p => `L ${p}`),
    `L ${chartWidth},${chartHeight}`,
    'Z'
  ].join(' ');

  // Calculate price change
  const firstPrice = data[0].close;
  const lastPrice = data[data.length - 1].close;
  const priceChange = lastPrice - firstPrice;
  const percentChange = (priceChange / firstPrice) * 100;
  const isPositive = priceChange >= 0;

  return (
    <div className="w-full">
      {/* Chart Stats */}
      <div className="flex justify-between items-center mb-4 px-4">
        <div>
          <div className="text-2xl font-bold text-white">
            ${lastPrice.toFixed(2)}
          </div>
          <div className={`text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{percentChange.toFixed(2)}%)
          </div>
        </div>
        <div className="text-right text-sm text-slate-400">
          <div>High: ${maxPrice.toFixed(2)}</div>
          <div>Low: ${minPrice.toFixed(2)}</div>
        </div>
      </div>

      {/* SVG Chart */}
      <div className="relative bg-slate-900/50 rounded-lg p-4 overflow-x-auto">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-64"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <defs>
            <linearGradient id={`gradient-${symbol}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0.3" />
              <stop offset="100%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Horizontal grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((percent, i) => (
            <line
              key={i}
              x1="0"
              y1={chartHeight * percent}
              x2={chartWidth}
              y2={chartHeight * percent}
              stroke="#334155"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          ))}

          {/* Area fill */}
          <path
            d={areaPoints}
            fill={`url(#gradient-${symbol})`}
          />

          {/* Price line */}
          <path
            d={pathData}
            fill="none"
            stroke={isPositive ? "#10b981" : "#ef4444"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {points.map((point, index) => {
            if (index % Math.ceil(pointCount / 20) !== 0 && index !== pointCount - 1) return null;
            const [x, y] = point.split(',').map(Number);
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="3"
                fill={isPositive ? "#10b981" : "#ef4444"}
                stroke="#fff"
                strokeWidth="1"
              />
            );
          })}
        </svg>

        {/* Date labels */}
        <div className="flex justify-between text-xs text-slate-400 mt-2">
          <span>{new Date(data[0].date).toLocaleDateString()}</span>
          <span>{new Date(data[Math.floor(data.length / 2)].date).toLocaleDateString()}</span>
          <span>{new Date(data[data.length - 1].date).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}
