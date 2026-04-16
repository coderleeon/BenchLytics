'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Zap, CheckCircle, AlertTriangle, DollarSign } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/leaderboard')
      .then(res => res.json())
      .then(d => {
        setData(d.leaderboard || []);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        // Mock data for display if backend is offline
        setData([
          { model: 'gemini-1.5-pro', avg_correctness: 9.2, avg_latency: 850, total_cost: 0.012, avg_hallucination_rate: 0.05 },
          { model: 'gpt-4o', avg_correctness: 9.1, avg_latency: 1100, total_cost: 0.045, avg_hallucination_rate: 0.08 }
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">Model Leaderboard</h1>
          <p className="text-muted-foreground mt-2">Aggregate performance across all benchmarked tasks</p>
        </div>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center border border-border rounded-xl">
          <div className="animate-pulse flex items-center gap-2"><Activity className="animate-spin"/> Loading data...</div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {data.slice(0, 4).map((model: any, i: number) => (
            <div key={model.model} className="glass rounded-xl p-6 relative overflow-hidden group hover:border-primary/50 transition-colors">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                #{i + 1}
              </div>
              <h3 className="font-semibold text-lg text-white mb-4">{model.model}</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-muted-foreground"><CheckCircle size={14}/> Correctness</span>
                  <span className="font-mono text-green-400">{model.avg_correctness}/10</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-muted-foreground"><Zap size={14}/> Latency</span>
                  <span className="font-mono">{model.avg_latency}ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-muted-foreground"><AlertTriangle size={14}/> Hallucination</span>
                  <span className="font-mono text-red-400">{(model.avg_hallucination_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-muted-foreground"><DollarSign size={14}/> Cost</span>
                  <span className="font-mono text-yellow-400">${model.total_cost.toFixed(4)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Trend Graph Section */}
      <div className="glass rounded-xl p-6 mt-8">
        <h2 className="text-xl font-bold mb-6">Performance Trends</h2>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="model" stroke="#a1a1aa" />
              <YAxis yAxisId="left" stroke="#4ade80" />
              <YAxis yAxisId="right" orientation="right" stroke="#ef4444" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px' }}
                itemStyle={{ color: '#fafafa' }}
              />
              <Line yAxisId="left" type="monotone" dataKey="avg_correctness" stroke="#4ade80" strokeWidth={2} name="Correctness" />
              <Line yAxisId="right" type="monotone" dataKey="avg_hallucination_rate" stroke="#ef4444" strokeWidth={2} name="Hallucination Rate" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
