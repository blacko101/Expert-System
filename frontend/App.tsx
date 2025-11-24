import React, { useState } from 'react';
import ContextPanel from './components/ContextPanel';
import ChatInterface from './components/ChatInterface';
import DiagnosisResult from './components/DiagnosisResult';
import { TechnicalContext, Message, ExpertDiagnosis, Domain } from './types';
import { sendChatMessage, analyzeContext, runExpertSystem } from './services/geminiService';

const App: React.FC = () => {
  // --- STATE ---
  const [domain, setDomain] = useState<Domain>(null);
  
  const [context, setContext] = useState<TechnicalContext>({
    domain: null,
    facts: {}
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [diagnosis, setDiagnosis] = useState<ExpertDiagnosis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // --- ACTIONS ---

  const handleDomainSelect = (selectedDomain: 'Network' | 'Computer') => {
    setDomain(selectedDomain);
    setContext({ domain: selectedDomain, facts: {} });
    setMessages([
      {
        id: 'welcome',
        role: 'model',
        content: selectedDomain === 'Network' 
          ? "Hello! I'm your Network Specialist. Are you having trouble with WiFi, Ethernet, or specific websites?"
          : "Hello! I'm your Hardware Specialist. Tell me about the symptoms (e.g., Blue Screen, overheating, beeping noises).",
        timestamp: Date.now()
      }
    ]);
  };

  const handleSendMessage = async (text: string) => {
    // 1. Add user message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp: Date.now() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setIsTyping(true);
    setIsAnalyzing(true);

    try {
      // 2. Parallel Process: Get Chat Reply AND Analyze for Data
      const [chatResponse, analysis] = await Promise.all([
        sendChatMessage(newHistory, context),
        analyzeContext(text, context)
      ]);

      // 3. Update Technical Context (Merge new facts with old facts)
      const updatedContext = { 
        ...context, 
        facts: { ...context.facts, ...analysis.technicalUpdates } 
      };
      
      setContext(updatedContext);

      // 4. Trigger Expert System Logic
      // If we have > 2 facts or Gemini thinks it's complete, we run a check
      const factCount = Object.keys(updatedContext.facts).length;
      
      if ((analysis.isComplete || factCount >= 3) && !diagnosis) {
         // Notify user
         const systemMsg: Message = {
           id: (Date.now() + 1).toString(),
           role: 'system',
           content: '<i>Updating expert analysis...</i>',
           timestamp: Date.now()
         };
         setMessages(prev => [...prev, systemMsg]);
         
         const result = await runExpertSystem(updatedContext);
         
         // Only set diagnosis if confidence is high enough to be useful, 
         // otherwise keep chatting
         if (result.confidence > 0.4) {
             setDiagnosis(result);
         }
      }

      // 5. Add AI Response
      const aiMsg: Message = {
        id: (Date.now() + 2).toString(),
        role: 'model',
        content: chatResponse,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, aiMsg]);

    } catch (error) {
      console.error("Pipeline Error", error);
    } finally {
      setIsTyping(false);
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setDomain(null);
    setContext({ domain: null, facts: {} });
    setDiagnosis(null);
    setMessages([]);
  };

  // --- RENDER: LANDING PAGE (TRIAGE) ---
  if (!domain) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-200 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent mb-4">
              NetWiz Expert System
            </h1>
            <p className="text-slate-400 text-lg">
              Select the category of your problem to initialize the appropriate diagnostic engine.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Network Card */}
            <button 
              onClick={() => handleDomainSelect('Network')}
              className="group relative bg-slate-800 p-8 rounded-2xl border border-slate-700 hover:border-blue-500 hover:bg-slate-750 transition-all duration-300 text-left shadow-xl hover:shadow-2xl hover:shadow-blue-500/10"
            >
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <svg className="w-32 h-32 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-blue-400">Network & Internet</h3>
              <p className="text-slate-400 mb-6">WiFi issues, slow internet, router configuration, DNS errors, or connectivity drops.</p>
              <span className="inline-flex items-center text-blue-400 font-semibold group-hover:translate-x-2 transition-transform">
                Start Diagnosis &rarr;
              </span>
            </button>

            {/* Hardware Card */}
            <button 
              onClick={() => handleDomainSelect('Computer')}
              className="group relative bg-slate-800 p-8 rounded-2xl border border-slate-700 hover:border-emerald-500 hover:bg-slate-750 transition-all duration-300 text-left shadow-xl hover:shadow-2xl hover:shadow-emerald-500/10"
            >
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <svg className="w-32 h-32 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-emerald-400">Computer Hardware</h3>
              <p className="text-slate-400 mb-6">Blue screens, overheating, strange noises, startup failures, or peripheral issues.</p>
              <span className="inline-flex items-center text-emerald-400 font-semibold group-hover:translate-x-2 transition-transform">
                Start Diagnosis &rarr;
              </span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDER: MAIN APP ---
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-4 md:p-8 flex items-center justify-center">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-6 h-[85vh]">
        
        {/* Left Column */}
        <div className="lg:col-span-4 flex flex-col gap-6 h-full">
           <div className="bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-700">
             <div className="flex justify-between items-start">
               <div>
                 <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                   NetWiz
                 </h1>
                 <span className="text-xs font-mono bg-slate-700 px-2 py-0.5 rounded text-slate-300">
                    Mode: {domain}
                 </span>
               </div>
               <button onClick={handleReset} className="text-xs text-slate-500 hover:text-white underline">
                 Change Mode
               </button>
             </div>
             <p className="text-slate-400 text-sm mt-2">
               Describe your issue. The AI will extract the facts required by the expert engine.
             </p>
           </div>
           
           <div className="flex-1 min-h-0">
             <ContextPanel context={context} isLoading={isAnalyzing} />
           </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-8 h-full flex flex-col">
          {diagnosis ? (
            <div className="h-full flex flex-col justify-center animate-fade-in-up">
               <DiagnosisResult diagnosis={diagnosis} onReset={() => setDiagnosis(null)} />
               <div className="mt-6 text-center">
                 <button onClick={() => setDiagnosis(null)} className="text-slate-500 text-sm hover:text-white transition-colors">
                   &larr; Return to conversation
                 </button>
               </div>
            </div>
          ) : (
            <ChatInterface 
              messages={messages} 
              onSendMessage={handleSendMessage} 
              isTyping={isTyping} 
            />
          )}
        </div>

      </div>
    </div>
  );
};

export default App;
