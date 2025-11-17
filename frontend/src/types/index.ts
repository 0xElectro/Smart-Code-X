export interface User {
  id: string;
  email: string;
  username: string;
  createdAt: string;
  avatar_url?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials extends LoginCredentials {
  username: string;
}

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface CodeIssue {
  id: string;
  file: string;
  line: number;
  column?: number;
  message: string;
  severity: Severity;
  category: 'quality' | 'security' | 'performance' | 'maintainability';
  suggestion?: string;
  code?: string;
}

export interface FileAnalysis {
  path: string;
  issues: CodeIssue[];
  linesOfCode: number;
  complexity: number;
  score: number;
}

export interface ReviewResult {
  id: string;
  projectName: string;
  createdAt: string;
  overallScore: number;
  totalFiles: number;
  totalIssues: number;
  issuesBySeverity: Record<Severity, number>;
  issuesByCategory: Record<CodeIssue['category'], number>;
  files: FileAnalysis[];
  summary: string;
}

export type ReviewStep = 'extracting' | 'analyzing' | 'reviewing' | 'generating';

export interface ReviewProgress {
  step: ReviewStep;
  progress: number;
  message: string;
}
