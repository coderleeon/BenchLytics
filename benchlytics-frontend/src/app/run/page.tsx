'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Settings2 } from 'lucide-react';

export default function RunBenchmark() {
  const router = useRouter();
  const [task, setTask] = useState('');
  const [models, setModels] = useState<string[]>([]);
  const [availableModels, setAvailableModels] = useState<string[]>(['gpt-4o', 'gemini-1.5-pro', 'gemini-1.5-flash']);
  const [iterations, setIterations] = useState(1);
  const [promptVar, setPromptVar] = useState('default');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/models')
      .then(res => res.json())
      .then(d => {
        if(d.models) setAvailableModels(d.models);
      })
      .catch(e => console.error("Failed to load models, using defaults."));
  }, []);

  const toggleModel = (id: string) => {
    setModels(prev => prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task || models.length === 0) return;
    
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, models, iterations, prompt_variation: promptVar })
      });
      const data = await res.json();
      if (data.experiment_id) {
        router.push(`/results/${data.experiment_id}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to connect to backend backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold">Run New Benchmark</h1>
        <p className="text-muted-foreground mt-2">Deploy a task across multiple evaluators to compare outputs</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 glass p-8 rounded-2xl">
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-300">Task Prompt</label>
          <textarea
            value={task}
            onChange={e => setTask(e.target.value)}
            placeholder="Write a python script to implement a linked list..."
            className="w-full h-32 px-4 py-3 bg-background border border-border rounded-xl focus:ring-2 focus:ring-primary focus:outline-none transition-all resize-none"
            required
          />
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-300">Select Models</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {availableModels.map(m => (
              <button
                type="button"
                key={m}
                onClick={() => toggleModel(m)}
                className={`p-3 rounded-xl border text-sm text-left transition-all ${
                  models.includes(m) ? 'border-primary bg-primary/10 text-white' : 'border-border text-muted-foreground hover:border-gray-500'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-border">
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
              <Settings2 size={16}/> Prompt Variation
            </label>
            <select
              value={promptVar}
              onChange={e => setPromptVar(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-border rounded-xl focus:ring-2 focus:ring-primary focus:outline-none"
            >
              <option value="default">Default</option>
              <option value="cot">Chain of Thought</option>
              <option value="zero-shot">Zero-shot</option>
            </select>
          </div>
          
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-300">Iterations (Multi-Run)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={iterations}
              onChange={e => setIterations(parseInt(e.target.value))}
              className="w-full px-4 py-3 bg-background border border-border rounded-xl focus:ring-2 focus:ring-primary focus:outline-none"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || models.length === 0 || !task}
          className="w-full py-4 mt-6 bg-white text-black font-semibold rounded-xl hover:bg-gray-200 focus:ring-4 focus:ring-gray-400 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <span className="animate-pulse">Starting Experiment...</span>
          ) : (
            <><Play size={18} fill="currentColor"/> Execute Benchmark</>
          )}
        </button>
      </form>
    </div>
  );
}
