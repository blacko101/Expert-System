// Domain selection
export type Domain = 'Network' | 'Computer' | null;

// The context now holds a flexible dictionary of facts
// This matches the Python Dict[str, Any] structure
export interface TechnicalContext {
  domain: Domain;
  facts: Record<string, any>; 
  // Examples of keys that might exist in 'facts':
  // Network: 'ping_latency', 'gateway_ping', 'packet_loss'
  // Computer: 'cpu_temp', 'beep_codes', 'blue_screen_code', 'ram_usage'
}

export interface Message {
  id: string;
  role: 'user' | 'model' | 'system';
  content: string;
  timestamp: number;
}

export interface ExpertDiagnosis {
  name: string;
  confidence: number;
  remedy: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  reasoning?: string;
  case_id?: number;
}

export interface AnalysisResult {
  technicalUpdates: Record<string, any>; // Updates to the facts dictionary
  isComplete: boolean;
}
