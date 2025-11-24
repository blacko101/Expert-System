import React from 'react';
import { TechnicalContext } from '../types';

interface ContextPanelProps {
  context: TechnicalContext;
  isLoading: boolean;
}

const ContextPanel: React.FC<ContextPanelProps> = ({ context, isLoading }) => {
  
  // Helper to format snake_case keys to Title Case (e.g. "cpu_temp" -> "Cpu Temp")
  const formatLabel = (key: string) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getStatusColor = (val: any) => {
    const s = String(val).toLowerCase();
    if (s === 'false' || s === 'fail' || s === 'unreachable' || s === 'down' || s === 'no') return 'text-red-400';
    if (s === 'true' || s === 'success' || s === 'reachable' || s === 'up' || s === 'yes') return 'text-emerald-400';
    if (!isNaN(Number(val))) return 'text-blue-300'; // Numbers
    return 'text-yellow-400';
  };

  const factsList = Object.entries(context.facts);

  return (
    <div className="bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-700 h-full flex flex-col">
      <div className="mb-4 border-b border-slate-700 pb-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
          </svg>
          {context.domain ? `${context.domain} Variables` : 'System State'}
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Real-time extraction of technical parameters.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
        {factsList.length === 0 ? (
          <div className="text-center py-10 text-slate-600 italic text-sm">
            Waiting for input...
            <br/>
            <span className="text-xs opacity-50">(e.g., "My ping is 250ms")</span>
          </div>
        ) : (
          factsList.map(([key, value]) => (
            <div key={key} className="flex justify-between items-center py-2 px-3 border-b border-slate-700/50 last:border-0 hover:bg-slate-700/30 rounded transition-colors group">
              <span className="text-slate-400 text-sm font-medium group-hover:text-slate-200 transition-colors">{formatLabel(key)}</span>
              <span className={`font-mono text-sm font-semibold ${getStatusColor(value)}`}>
                {String(value)}
              </span>
            </div>
          ))
        )}
      </div>

      {isLoading && (
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center gap-3 animate-pulse">
          <div className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin"></div>
          <span className="text-xs text-blue-300">Analyzing input against rules...</span>
        </div>
      )}
    </div>
  );
};

export default ContextPanel;