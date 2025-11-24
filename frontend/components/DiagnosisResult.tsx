import React from 'react';
import { ExpertDiagnosis } from '../types';

interface DiagnosisResultProps {
  diagnosis: ExpertDiagnosis;
  onReset: () => void;
}

const DiagnosisResult: React.FC<DiagnosisResultProps> = ({ diagnosis, onReset }) => {
  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'Critical': return 'bg-red-500 text-white';
      case 'High': return 'bg-orange-500 text-white';
      case 'Medium': return 'bg-yellow-500 text-black';
      default: return 'bg-blue-500 text-white';
    }
  };

  return (
    <div className="mt-6 bg-slate-800 rounded-xl overflow-hidden shadow-2xl border border-slate-600 animate-fade-in-up">
      <div className={`p-4 ${getSeverityColor(diagnosis.severity)} flex justify-between items-center`}>
        <h3 className="font-bold text-lg">Expert Diagnosis Complete</h3>
        <span className="text-xs font-mono uppercase bg-black/20 px-2 py-1 rounded">
          Severity: {diagnosis.severity}
        </span>
      </div>
      
      <div className="p-6">
        <div className="mb-6">
          <label className="text-xs text-slate-400 uppercase tracking-wide font-bold">Identified Issue</label>
          <div className="text-2xl font-bold text-white mt-1">{diagnosis.name}</div>
          <div className="text-sm text-slate-400 mt-1">Confidence: {(diagnosis.confidence * 100).toFixed(1)}%</div>
        </div>

        {/* Reasoning Section (Explainable AI) */}
        {diagnosis.reasoning && (
          <div className="mb-6 bg-slate-900/30 rounded-lg p-3 border border-slate-700/50">
             <label className="text-xs text-slate-500 uppercase tracking-wide font-bold flex items-center gap-2 mb-1">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                 <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
               </svg>
               Logic Trace
             </label>
             <p className="text-sm text-slate-300 italic font-mono">
               "{diagnosis.reasoning}"
             </p>
          </div>
        )}

        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
          <label className="text-xs text-blue-400 uppercase tracking-wide font-bold flex items-center gap-2">
             <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.381z" clipRule="evenodd" />
            </svg>
            Recommended Remedy
          </label>
          <p className="text-slate-200 mt-2 leading-relaxed">
            {diagnosis.remedy}
          </p>
        </div>

        <button 
          onClick={onReset}
          className="mt-6 w-full py-3 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors font-medium text-sm"
        >
          Start New Diagnosis
        </button>
      </div>
    </div>
  );
};

export default DiagnosisResult;