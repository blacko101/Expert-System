"""
NLP Processor for extracting technical facts from user input
Production-ready version with comprehensive error handling
"""
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class NLPProcessor:
    """Natural Language Processor for technical fact extraction"""
    
    def __init__(self):
        self.patterns = {
            'number': r'\b\d+(?:\.\d+)?\b',
            'percentage': r'\b\d+(?:\.\d+)?%\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'speed': r'(\d+(?:\.\d+)?)\s*(mbps|mb/s|mb|kbps|kb/s)',
            'latency': r'(\d+(?:\.\d+)?)\s*(ms|milliseconds?)',
            'temperature': r'(\d+(?:\.\d+)?)\s*(°?c|celsius|°?f|fahrenheit)',
        }
        
        self.keywords = {
            'network': {
                'ping': ['ping', 'latency', 'response time'],
                'speed': ['speed', 'bandwidth', 'throughput', 'mbps'],
                'connection': ['connect', 'disconnect', 'drop', 'stable', 'unstable'],
                'wifi': ['wifi', 'wireless', 'wi-fi'],
                'ethernet': ['ethernet', 'wired', 'cable'],
                'router': ['router', 'gateway', 'modem'],
                'dns': ['dns', 'domain', 'website'],
                'ip': ['ip', 'address', '192.168', '10.0'],
            },
            'computer': {
                'temperature': ['temp', 'temperature', 'hot', 'overheat', 'cool'],
                'power': ['power', 'turn on', 'start', 'boot'],
                'display': ['screen', 'display', 'monitor', 'black', 'blank'],
                'performance': ['slow', 'lag', 'freeze', 'crash', 'hang'],
                'sound': ['beep', 'noise', 'sound', 'click', 'grind'],
                'memory': ['memory', 'ram', 'out of memory'],
                'disk': ['disk', 'hard drive', 'ssd', 'storage'],
            }
        }
        
        self.domain_mapping = {
            'network': 'Network',
            'computer': 'Computer',
            'hardware': 'Computer',
            'software': 'Computer',
            'internet': 'Network',
            'wifi': 'Network',
            'ethernet': 'Network',
        }
    
    def extract_facts(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract technical facts from user input with error handling
        
        Args:
            text: User input text
            context: Current context including domain and existing facts
            
        Returns:
            Dictionary of extracted facts
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning(f"Invalid text input: {text}")
                return {}
            
            text_lower = text.lower()
            extracted = {}
            
            # Determine domain if not already set
            if not context.get('domain'):
                extracted['domain'] = self._detect_domain(text_lower)
            
            # Extract based on detected or existing domain
            domain = context.get('domain') or extracted.get('domain')
            
            if domain == 'Network':
                self._extract_network_facts(text_lower, extracted)
            elif domain == 'Computer':
                self._extract_computer_facts(text_lower, extracted)
            else:
                # Try both if domain unknown
                self._extract_network_facts(text_lower, extracted)
                self._extract_computer_facts(text_lower, extracted)
            
            # Extract numeric values
            self._extract_numeric_values(text, extracted)
            
            # Extract boolean states
            self._extract_boolean_states(text_lower, extracted)
            
            # Clean up extracted facts
            self._clean_extracted_facts(extracted)
            
            logger.debug(f"Extracted facts from '{text}': {extracted}")
            return extracted
            
        except Exception as e:
            logger.error(f"Error extracting facts from text '{text}': {str(e)}", exc_info=True)
            return {}
    
    def is_complete_for_diagnosis(self, facts: Dict[str, Any], domain: Optional[str] = None) -> bool:
        """
        Check if we have enough facts for a diagnosis
        
        Args:
            facts: Current facts dictionary
            domain: Problem domain
            
        Returns:
            True if sufficient facts for diagnosis
        """
        try:
            if not facts:
                return False
            
            fact_count = len(facts)
            
            # Determine domain from facts if not provided
            if not domain:
                domain = facts.get('domain')
            
            if domain == 'Network':
                # Network diagnosis requires at least 2 key facts
                key_facts = ['ping_latency', 'speed_mbps', 'gateway_ping', 'wifi_connected', 'eth_link']
                present_key_facts = sum(1 for kf in key_facts if kf in facts)
                return fact_count >= 3 or present_key_facts >= 2
                
            elif domain == 'Computer':
                # Computer diagnosis requires at least 2 key facts
                key_facts = ['cpu_temp', 'pc_power', 'display', 'slow_performance', 'beep_codes']
                present_key_facts = sum(1 for kf in key_facts if kf in facts)
                return fact_count >= 3 or present_key_facts >= 2
            
            # If domain unknown, require more facts
            return fact_count >= 4
            
        except Exception as e:
            logger.error(f"Error checking diagnosis completeness: {str(e)}", exc_info=True)
            return False
    
    def suggest_questions(self, facts: Dict[str, Any], domain: Optional[str] = None) -> List[str]:
        """
        Generate follow-up questions based on missing information
        
        Args:
            facts: Current facts dictionary
            domain: Problem domain
            
        Returns:
            List of suggested questions
        """
        try:
            questions = []
            
            if not facts:
                facts = {}
            
            if not domain:
                domain = facts.get('domain')
            
            if domain == 'Network':
                if 'ping_latency' not in facts:
                    questions.append("What is your ping latency in milliseconds?")
                if 'speed_mbps' not in facts:
                    questions.append("What's your internet speed in Mbps?")
                if 'gateway_ping' not in facts:
                    questions.append("Can you ping your router/gateway?")
                if 'wifi_connected' not in facts:
                    questions.append("Are you connected via WiFi or Ethernet?")
                if len(questions) == 0 and 'packet_loss' not in facts:
                    questions.append("Are you experiencing any packet loss?")
                    
            elif domain == 'Computer':
                if 'pc_power' not in facts:
                    questions.append("Is the computer powering on?")
                if 'display' not in facts:
                    questions.append("Do you see anything on the display?")
                if 'cpu_temp' not in facts:
                    questions.append("What's the CPU temperature?")
                if 'slow_performance' not in facts:
                    questions.append("Is the system running slower than usual?")
                if len(questions) == 0 and 'beep_codes' not in facts:
                    questions.append("Are there any beep codes or unusual sounds?")
            
            # Limit to 3 questions
            return questions[:3]
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}", exc_info=True)
            return ["Could you provide more details about the issue?"]
    
    # ============ PRIVATE HELPER METHODS ============
    
    def _detect_domain(self, text: str) -> str:
        """Detect problem domain from text"""
        try:
            text_lower = text.lower()
            
            network_score = 0
            computer_score = 0
            
            # Check for network keywords
            for category in self.keywords['network'].values():
                for keyword in category:
                    if keyword in text_lower:
                        network_score += 1
            
            # Check for computer keywords
            for category in self.keywords['computer'].values():
                for keyword in category:
                    if keyword in text_lower:
                        computer_score += 1
            
            # Check explicit domain mentions
            if any(word in text_lower for word in ['network', 'internet', 'wifi', 'ethernet', 'router']):
                network_score += 2
            
            if any(word in text_lower for word in ['computer', 'pc', 'hardware', 'software', 'windows']):
                computer_score += 2
            
            if network_score > computer_score:
                return 'Network'
            elif computer_score > network_score:
                return 'Computer'
            else:
                # Default to Network if ambiguous
                return 'Network'
                
        except Exception as e:
            logger.error(f"Error detecting domain: {str(e)}", exc_info=True)
            return 'Network'
    
    def _extract_network_facts(self, text: str, extracted: Dict[str, Any]):
        """Extract network-related facts with error handling"""
        try:
            # Ping/Latency
            if any(word in text for word in ['ping', 'latency', 'ms', 'millisecond']):
                numbers = re.findall(self.patterns['number'], text)
                if numbers:
                    try:
                        extracted['ping_latency'] = float(numbers[0])
                    except (ValueError, TypeError):
                        pass
            
            # Speed
            if any(word in text for word in ['speed', 'mbps', 'bandwidth', 'internet speed']):
                speed_match = re.search(self.patterns['speed'], text, re.IGNORECASE)
                if speed_match:
                    try:
                        speed = float(speed_match.group(1))
                        unit = speed_match.group(2).lower()
                        # Convert to Mbps
                        if 'k' in unit:
                            speed = speed / 1000
                        extracted['speed_mbps'] = speed
                    except (ValueError, AttributeError, TypeError):
                        pass
            
            # Connection status
            if 'wifi' in text or 'wireless' in text:
                if any(word in text for word in ['not connect', 'disconnect', 'drop', 'no wifi']):
                    extracted['wifi_connected'] = False
                elif any(word in text for word in ['connect', 'connected', 'working wifi']):
                    extracted['wifi_connected'] = True
            
            # Gateway/Router
            if any(word in text for word in ['router', 'gateway', 'modem']):
                if any(word in text for word in ['not ping', 'cant ping', 'ping fail']):
                    extracted['gateway_ping'] = 'fail'
                elif 'ping' in text:
                    extracted['gateway_ping'] = 'success'
            
            # DNS
            if any(word in text for word in ['dns', 'website', 'domain']):
                if any(word in text for word in ['not work', 'not load', 'cant access']):
                    extracted['ping_domain'] = 'fail'
                elif 'ping' in text:
                    extracted['ping_domain'] = 'success'
            
            # Ethernet
            if any(word in text for word in ['ethernet', 'wired', 'cable']):
                if any(word in text for word in ['not work', 'down', 'disconnect']):
                    extracted['eth_link'] = 'down'
                else:
                    extracted['eth_link'] = 'up'
                    
        except Exception as e:
            logger.error(f"Error extracting network facts: {str(e)}", exc_info=True)
    
    def _extract_computer_facts(self, text: str, extracted: Dict[str, Any]):
        """Extract computer-related facts with error handling"""
        try:
            # Temperature
            if any(word in text for word in ['temp', 'temperature', 'hot', 'overheat']):
                temp_match = re.search(self.patterns['temperature'], text, re.IGNORECASE)
                if temp_match:
                    try:
                        temp = float(temp_match.group(1))
                        unit = temp_match.group(2).lower()
                        # Convert to Celsius if needed
                        if 'f' in unit:
                            temp = (temp - 32) * 5/9
                        extracted['cpu_temp'] = temp
                    except (ValueError, AttributeError, TypeError):
                        extracted['cpu_temp'] = 85  # Default high temp
                else:
                    # Mention of overheating without specific temp
                    extracted['cpu_temp'] = 85
            
            # Power
            if any(word in text for word in ['power', 'turn on', 'start', 'boot']):
                if any(word in text for word in ['not power', 'wont turn', 'no power', 'dead']):
                    extracted['pc_power'] = False
                else:
                    extracted['pc_power'] = True
            
            # Display
            if any(word in text for word in ['screen', 'display', 'monitor']):
                if any(word in text for word in ['not show', 'blank', 'black', 'no display']):
                    extracted['display'] = 'no'
                else:
                    extracted['display'] = 'yes'
            
            # Performance
            if any(word in text for word in ['slow', 'lag', 'freeze', 'unresponsive']):
                extracted['slow_performance'] = True
            
            # Beep codes
            if 'beep' in text:
                if 'memory' in text or 'ram' in text:
                    extracted['beep_codes'] = 'mem'
                elif 'graphics' in text or 'gpu' in text:
                    extracted['beep_codes'] = 'gpu'
                else:
                    extracted['beep_codes'] = 'unknown'
                    
        except Exception as e:
            logger.error(f"Error extracting computer facts: {str(e)}", exc_info=True)
    
    def _extract_numeric_values(self, text: str, extracted: Dict[str, Any]):
        """Extract general numeric values with error handling"""
        try:
            numbers = re.findall(self.patterns['number'], text)
            for i, num_str in enumerate(numbers):
                try:
                    num = float(num_str)
                    # Assign to common fields if not already set
                    if i == 0 and 'ping_latency' not in extracted:
                        extracted['ping_latency'] = num
                    elif i == 1 and 'speed_mbps' not in extracted and num < 1000:
                        extracted['speed_mbps'] = num
                    elif i == 2 and 'cpu_temp' not in extracted and num < 200:
                        extracted['cpu_temp'] = num
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            logger.error(f"Error extracting numeric values: {str(e)}", exc_info=True)
    
    def _extract_boolean_states(self, text: str, extracted: Dict[str, Any]):
        """Extract yes/no/true/false states with error handling"""
        try:
            # Positive indicators
            if any(word in text for word in ['yes', 'works', 'working', 'connected', 'up', 'ok', 'fine']):
                # Set positive states for relevant fields
                if 'wifi' in text and 'wifi_connected' not in extracted:
                    extracted['wifi_connected'] = True
                if 'ethernet' in text and 'eth_link' not in extracted:
                    extracted['eth_link'] = 'up'
                if 'power' in text and 'pc_power' not in extracted:
                    extracted['pc_power'] = True
            
            # Negative indicators
            if any(word in text for word in ['no', 'not', 'doesnt', 'wont', 'cant', 'failed', 'down']):
                # Set negative states for relevant fields
                if 'wifi' in text and 'wifi_connected' not in extracted:
                    extracted['wifi_connected'] = False
                if 'ethernet' in text and 'eth_link' not in extracted:
                    extracted['eth_link'] = 'down'
                if 'power' in text and 'pc_power' not in extracted:
                    extracted['pc_power'] = False
                    
        except Exception as e:
            logger.error(f"Error extracting boolean states: {str(e)}", exc_info=True)
    
    def _clean_extracted_facts(self, extracted: Dict[str, Any]):
        """Clean and validate extracted facts with error handling"""
        try:
            # Remove None values
            keys_to_remove = []
            for key, value in extracted.items():
                if value is None:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del extracted[key]
            
            # Validate numeric ranges
            if 'ping_latency' in extracted:
                try:
                    val = float(extracted['ping_latency'])
                    if val < 0 or val > 10000:  # Unreasonable ping
                        del extracted['ping_latency']
                except (ValueError, TypeError):
                    del extracted['ping_latency']
            
            if 'speed_mbps' in extracted:
                try:
                    val = float(extracted['speed_mbps'])
                    if val < 0 or val > 10000:  # Unreasonable speed
                        del extracted['speed_mbps']
                except (ValueError, TypeError):
                    del extracted['speed_mbps']
            
            if 'cpu_temp' in extracted:
                try:
                    val = float(extracted['cpu_temp'])
                    if val < 0 or val > 200:  # Unreasonable temperature
                        del extracted['cpu_temp']
                except (ValueError, TypeError):
                    del extracted['cpu_temp']
                    
        except Exception as e:
            logger.error(f"Error cleaning extracted facts: {str(e)}", exc_info=True)
    
    def validate_input(self, text: str) -> tuple[bool, str]:
        """
        Validate user input text
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not text or not isinstance(text, str):
                return False, "Input text is required and must be a string"
            
            if len(text.strip()) < 3:
                return False, "Input text is too short (minimum 3 characters)"
            
            if len(text) > 1000:
                return False, "Input text is too long (maximum 1000 characters)"
            
            # Check for potentially malicious content
            if any(char in text for char in ['<script>', '</script>', 'javascript:', 'onload=']):
                return False, "Input contains potentially unsafe content"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating input: {str(e)}", exc_info=True)
            return False, f"Input validation error: {str(e)}"