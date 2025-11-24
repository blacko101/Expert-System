import { GoogleGenAI, Type } from "@google/genai";
import { TechnicalContext, AnalysisResult, Message, ExpertDiagnosis, Domain } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
const DJANGO_API_URL = 'http://localhost:8000/support/api/diagnose/'; 

// Keys extracted from your expert_engine.py
const NETWORK_KEYS = `
- ping_latency (number)
- speed_mbps (number)
- gateway_ping ('success'|'fail')
- ping_ip ('success'|'fail')
- ping_domain ('success'|'fail')
- wifi_connected (boolean)
- packet_loss (number)
- ip_address (string)
- ip_conflict_msg (boolean)
- wifi_auth_fail (boolean)
- eth_link ('up'|'down')
- multiple_users_down (boolean)
- internet_status_external ('up'|'down')
- rssi (number)
- ap_client_count (number)
- inbound_unreachable (boolean)
- browser_err ('proxy_required'|'proxy_auth'|string)
- switch_port_status ('disabled'|'active')
- vlan_mismatch (boolean)
- unexpected_dns_ip (boolean)
- mtu_fail (boolean)
- vpn_status ('up'|'down')
- dns_latency_ms (number)
- router_cpu (number)
- speed_variance (boolean)
- ipv6_error (boolean)
- arp_conflict (boolean)
- captive_portal (boolean)
- firewall_block (boolean)
- roam_count (number)
- switch_errors (number)
- gateway_correct (boolean)
- latency_internet (number)
- latency_intranet (number)
- dns_ttl (number)
- traceroute_loop (boolean)
- arp_flood (boolean)
- ssid_secure (boolean)
- driver_error_count (number)
- route_missing (boolean)
- ap_reboot (boolean)
- nat_mismatch (boolean)
- windows_profile ('Public'|'Private')
- https_cert_err (boolean)
- dns_hijack (boolean)
- qos_issues (boolean)
- duplex_mismatch (boolean)
- mtu_blackhole (boolean)
- arp_spoof_detected (boolean)
- ntp_ok (boolean)
- ssdp_flood (boolean)
- port_scan (boolean)
- router_config_good (boolean)
- old_ap_hw (boolean)
- client_online_via ('mobile'|'wifi'|'wired')
- content_filter_block (boolean)
- as_path_latency (number)
- legacy_rate_enabled (boolean)
`;

const COMPUTER_KEYS = `
- pc_power (boolean)
- display ('yes'|'no')
- beep_codes (string)
- cpu_temp (number)
- slow_performance (boolean)
- disk_health (number)
- boot_error (string)
- os_present (boolean)
- slow_boot (boolean)
- disk_usage_startup (number)
- app_crash (boolean)
- ram_usage (number)
- app_reinstall_attempted (boolean)
- popups (boolean)
- idle_cpu (number)
- files_encrypted (boolean)
- driver_conflict (boolean)
- gpu_reset (boolean)
- battery_health (number)
- fan_speed_ok (boolean)
- sudden_shutdown (boolean)
- power_bad_report (boolean)
- sfc_errors (number)
- recent_update (boolean)
- issue_started_after_update (boolean)
- chkdsk_errors (number)
- usb_error (boolean)
- bios_reset_detected (boolean)
- win_activate_err (boolean)
- expected_workload ('normal'|'high')
- browser_crash (boolean)
- browser_profile_old (boolean)
- background_cpu (number)
- core_temp_delta (number)
- ssd_trim_enabled (boolean)
- profile_corrupt (boolean)
- sleep_wake_fail (boolean)
- temp_sensor_err (boolean)
- firmware_old (boolean)
- app_cache_corrupt (boolean)
- kernel_panic_device (boolean)
- hdd_fragmentation (number)
- boot_sector_ok (boolean)
- gpo_block (boolean)
- vuln_found (boolean)
- network_stack_corrupt (boolean)
- auto_update_running (boolean)
- disk_free_percent (number)
- registry_errors (number)
- kernel_hang (boolean)
`;

// 1. CHAT FUNCTION
export const sendChatMessage = async (
  history: Message[],
  currentContext: TechnicalContext
): Promise<string> => {
  try {
    const previousHistory = history.slice(0, -1);
    const lastMsg = history[history.length - 1];

    const chatHistory = previousHistory.map(h => ({
      role: h.role === 'model' ? 'model' : 'user',
      parts: [{ text: h.content }]
    }));

    // Dynamic System Instruction based on Domain
    let domainInstruction = "";
    if (currentContext.domain === 'Network') {
      domainInstruction = "Focus on network connectivity, IP addresses, DNS, latency, and router details.";
    } else {
      domainInstruction = "Focus on hardware symptoms like beep codes, screen artifacts, temperature, noises, and power issues.";
    }

    const chat = ai.chats.create({
      model: "gemini-2.5-flash",
      config: {
        systemInstruction: `
          You are "NetWiz", an expert IT support agent.
          Current Domain: ${currentContext.domain} Troubleshooting.
          ${domainInstruction}
          
          Current Known Facts: ${JSON.stringify(currentContext.facts)}
          
          Goal: Help the user check technical details so the expert system can diagnose the issue.
          
          Rules:
          1. **Translation**: The user is likely non-technical. Translate technical terms into simple checks (e.g. "Gateway Unreachable" -> "Can you try pinging your router IP?").
          2. **Step-by-Step**: When asking for values (like Ping, IP Config, or CPU Temp), explain HOW to get them on their OS.
          3. **Conciseness**: Keep responses short.
          
          Do NOT output JSON here. Just talk to the user.
        `,
      },
      history: chatHistory,
    });

    const result = await chat.sendMessage({ message: lastMsg.content });
    return result.text || "I'm having trouble thinking right now.";

  } catch (error) {
    console.error("Chat Error:", error);
    return "Connection error.";
  }
};

// 2. EXTRACTION FUNCTION
export const analyzeContext = async (
  userMessage: string,
  currentContext: TechnicalContext
): Promise<AnalysisResult> => {
  try {
    const keysList = currentContext.domain === 'Network' ? NETWORK_KEYS : COMPUTER_KEYS;

    const prompt = `
      You are a precise data extraction engine for a Python Expert System.
      
      Domain: ${currentContext.domain}
      User Message: "${userMessage}"
      Current Facts: ${JSON.stringify(currentContext.facts)}

      Task: Extract technical facts from the message to populate the expert system variables.
      
      AVAILABLE VARIABLE KEYS (Strict Snake Case):
      ${keysList}

      Instructions:
      1. Map the user's description to the closest matching key above.
      2. If the user implies a boolean (e.g. "It's definitely overheating"), set the key (cpu_temp) to a value that triggers the rule (e.g. 90) or the boolean flag (e.g. overheating=true if such a key existed, but check the list).
      3. Extract numbers carefully.
      
      Output JSON format:
      {
        "technicalUpdates": {
           // key-value pairs of extracted facts, e.g. "ping_latency": 250
        },
        "isComplete": boolean // true if sufficient data for diagnosis seems present
      }
    `;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        // Schema removed to allow dynamic keys in technicalUpdates without strict "properties" definition
      }
    });

    const text = response.text;
    if (!text) return { technicalUpdates: {}, isComplete: false };
    
    return JSON.parse(text) as AnalysisResult;

  } catch (error) {
    console.error("Analysis Error:", error);
    return { technicalUpdates: {}, isComplete: false };
  }
};

// 3. EXPERT SYSTEM INTEGRATION
export const runExpertSystem = async (context: TechnicalContext): Promise<ExpertDiagnosis> => {
  try {
    // Send to Django
    const response = await fetch(DJANGO_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(context),
    });

    if (response.ok) {
      return await response.json();
    } 
    console.warn("Django offline or error, falling back to simulation.");
  } catch (error) {
    console.warn("Django connection failed, using simulation.");
  }

  return simulateExpertSystem(context);
};

const simulateExpertSystem = async (context: TechnicalContext): Promise<ExpertDiagnosis> => {
  await new Promise(resolve => setTimeout(resolve, 1500)); 

  const prompt = `
    Act as the Expert Engine (Fall back mode).
    Domain: ${context.domain}
    Facts: ${JSON.stringify(context.facts)}
    
    Diagnose the problem based on standard IT troubleshooting rules.
    Return JSON matching the ExpertDiagnosis interface.
    Include a 'reasoning' field explaining which facts triggered the diagnosis.
  `;

  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          name: { type: Type.STRING },
          confidence: { type: Type.NUMBER },
          remedy: { type: Type.STRING },
          severity: { type: Type.STRING, enum: ['Low', 'Medium', 'High', 'Critical'] },
          reasoning: { type: Type.STRING }
        }
      }
    }
  });

  const text = response.text;
  if (!text) throw new Error("Simulated diagnosis failed");
  return JSON.parse(text);
};
