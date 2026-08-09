export interface DocumentFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadDate: Date;
  status: 'uploading' | 'analyzing' | 'compliant' | 'non-compliant' | 'partial';
  complianceScore?: number;
  normesChecked?: string[];
  issues?: ComplianceIssue[];
  file?: File;
}

export interface ComplianceIssue {
  id: string;
  severity: 'critical' | 'major' | 'minor' | 'info';
  normeRef: string;
  description: string;
  page?: number;
  suggestion?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: Date;
  attachedDocument?: DocumentFile;
  complianceReport?: ComplianceReport;
  isTyping?: boolean;
}

export interface ComplianceReport {
  documentId: string;
  documentName: string;
  overallScore: number;
  status: 'compliant' | 'non-compliant' | 'partial';
  normesCovered: NormeResult[];
  totalIssues: number;
  criticalIssues: number;
  summary: string;
}

export interface NormeResult {
  normeName: string;
  normeCode: string;
  passed: boolean;
  score: number;
  details: string;
}

export interface ConversationHistory {
  id: string;
  title: string;
  lastMessage: string;
  date: Date;
  documentsCount: number;
  status: 'compliant' | 'non-compliant' | 'partial' | 'pending';
}