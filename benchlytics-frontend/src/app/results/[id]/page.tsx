'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Activity, Clock, FileCode2, ShieldAlert, CheckCircle, Zap } from 'lucide-react';

export default function ResultsView() {
  const params = useParams();
  const [data, setData] = useState<{ status: string; results: any[] } | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    const fetchResults = () => {
      fetch(`http://localhost:8000/api/experiments/${params.id}`)
        .then(res => res.json())
        .then(d => {
          setData(d);
          if (d.status === 'completed' || d.status === 'failed') {
            clearInterval(interval);
          }
        })
        .catch(console.error);
    };

    fetchResults();
    interval = setInterval(fetchResults, 2000); // Polling

    return () => clearInterval(interval);
  }, [params.id]);

  if (!data) return (
    <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
      <Activity className="animate-spin text-primary" size={32}/>
      <p className="text-muted-foreground animate-pulse">Initializing Dashboard...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end border-b border-border pb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            Experiment Results <span className="text-muted-foreground text-lg">#{params.id}</span>
          </h1>
          <div className="flex gap-4 mt-3">
            <span className={`px-3 py-1 text-xs font-medium rounded-full ${data.status === 'completed' ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-500'}`}>
              {data.status.toUpperCase()}
            </span>
            {data.status === 'running' && (
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <Clock size={14} className="animate-pulse" /> Evaluating models...
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {data.results.map((res: any, i: number) => {
          const radarData = [
            { subject: 'Correctness', A: res.score_correctness * 10, fullMark: 100 },
            { subject: 'Clarity', A: res.score_clarity * 10, fullMark: 100 },
            { subject: 'Reasoning', A: res.score_reasoning * 10, fullMark: 100 },
            { subject: 'Confidence', A: res.confidence_score * 10, fullMark: 100 },
          ];

          return (
            <div key={i} className="glass rounded-xl p-6 flex flex-col gap-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold">{res.model_name}</h3>
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-background border border-border rounded-md text-xs font-mono flex items-center gap-1">
                    <Zap size={10}/> {res.latency_ms.toFixed(0)}ms
                  </span>
                  <span className="px-2 py-1 bg-background border border-border rounded-md text-xs font-mono flex items-center gap-1">
                    💰 ${res.cost.toFixed(5)}
                  </span>
                </div>
              </div>

              {res.hallucination_flag === 1 && (
                <div className="bg-red-500/10 text-red-500 border border-red-500/20 p-3 rounded-lg text-sm flex items-start gap-2">
                  <ShieldAlert size={16} className="mt-0.5 shrink-0" />
                  <p><strong>Hallucination Detected:</strong> The judge flagged this response as containing ungrounded or fabricated statements.</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                      <PolarGrid stroke="#27272a" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <Radar name="Score" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                      <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px', fontSize: '12px' }} itemStyle={{ color: '#fafafa' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="flex flex-col justify-center gap-3">
                  <div className="glass p-3 rounded-lg shadow-sm border border-border/50">
                    <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Tokens Used</div>
                    <div className="text-lg font-mono">{res.token_count}</div>
                  </div>
                  <div className="glass p-3 rounded-lg shadow-sm border border-border/50">
                    <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Avg Score</div>
                    <div className="text-xl font-bold text-green-400">
                      {((res.score_correctness + res.score_clarity + res.score_reasoning) / 3).toFixed(1)} <span className="text-sm font-normal text-muted-foreground">/ 10</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-hidden mt-2">
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2"><FileCode2 size={16}/> Generated Output</h4>
                <div className="bg-background rounded-xl p-4 border border-border h-64 overflow-y-auto text-sm leading-relaxed text-gray-300 font-mono whitespace-pre-wrap">
                  {res.output || "No output generated..."}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
