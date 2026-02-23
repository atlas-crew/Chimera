export const ATTACK_LOG_EVENT = 'chimera:attack-log';

export interface AttackLog {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  payload: string;
  type: string;
  status: 'blocked' | 'allowed';
  source_ip: string;
}

export interface Objective {
  id: string;
  title: string;
  description: string;
  type: string;
  path?: string;
  payloadMatch?: string;
  statusPattern?: 'blocked' | 'allowed';
}

export const KILL_CHAIN_OBJECTIVES: Objective[] = [
  {
    id: 'recon_ai',
    title: 'OSINT: AI System Prompt',
    description: 'Trick the AI Assistant into revealing its internal system instructions.',
    type: 'GenAI',
    payloadMatch: 'system prompt'
  },
  {
    id: 'exploit_sqli',
    title: 'Exploit: SQL Injection',
    description: 'Use a SQL injection payload to bypass filters or extract data from any portal.',
    type: 'SQLi',
    statusPattern: 'allowed'
  },
  {
    id: 'access_ssrf',
    title: 'Lateral: Agent SSRF',
    description: 'Command the AI Agent to browse an internal metadata service (169.254.169.254).',
    type: 'SSRF',
    payloadMatch: '169.254.169.254'
  },
  {
    id: 'exfil_rag',
    title: 'Exfil: Malicious RAG',
    description: 'Upload a file with a path traversal name to write outside the sandbox.',
    type: 'FileUpload',
    payloadMatch: '..'
  }
];
