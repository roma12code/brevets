import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { DocumentService } from '../../services/document.service';
import { DocumentFile, ComplianceIssue } from '../../models/models';

@Component({
  selector: 'app-document-preview',
  standalone: false,
  templateUrl: './document-preview.component.html',
  styleUrls: ['./document-preview.component.css']
})
export class DocumentPreviewComponent implements OnInit {
  @Input() isOpen = false;
  @Output() closePreview = new EventEmitter<void>();

  currentDocument: DocumentFile | null = null;
  selectedNormes: string[] = [];
  activeTab: 'issues' | 'normes' | 'settings' = 'issues';

  constructor(public documentService: DocumentService) {}

  ngOnInit(): void {
    this.documentService.currentDocument$.subscribe(doc => {
      this.currentDocument = doc;
    });
    this.documentService.selectedNormes$.subscribe(normes => {
      this.selectedNormes = [...normes];
    });
  }

  close(): void {
    this.closePreview.emit();
  }

  setActiveTab(tab: 'issues' | 'normes' | 'settings'): void {
    this.activeTab = tab;
  }

  getSeverityClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'severity-critical';
      case 'major': return 'severity-major';
      case 'minor': return 'severity-minor';
      default: return 'severity-info';
    }
  }

  getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': return '🔴';
      case 'major': return '🟠';
      case 'minor': return '🟡';
      default: return '🔵';
    }
  }

  getSeverityLabel(severity: string): string {
    switch (severity) {
      case 'critical': return 'Critique';
      case 'major': return 'Majeur';
      case 'minor': return 'Mineur';
      default: return 'Info';
    }
  }

  getScoreClass(score: number | undefined): string {
    if (!score) return '';
    if (score >= 90) return 'score-high';
    if (score >= 70) return 'score-medium';
    return 'score-low';
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'compliant': return 'Conforme';
      case 'non-compliant': return 'Non conforme';
      case 'partial': return 'Partiel';
      case 'analyzing': return 'Analyse...';
      default: return 'Upload...';
    }
  }

  toggleNorme(normeCode: string): void {
    const idx = this.selectedNormes.indexOf(normeCode);
    if (idx > -1) {
      this.selectedNormes.splice(idx, 1);
    } else {
      this.selectedNormes.push(normeCode);
    }
    this.documentService.setSelectedNormes([...this.selectedNormes]);
  }

  isNormeSelected(normeCode: string): boolean {
    return this.selectedNormes.includes(normeCode);
  }

  formatFileSize(bytes: number): string {
    return this.documentService.formatFileSize(bytes);
  }

  getIssuesByCategory(): { [key: string]: ComplianceIssue[] } {
    if (!this.currentDocument?.issues) return {};
    const grouped: { [key: string]: ComplianceIssue[] } = {};
    this.currentDocument.issues.forEach(issue => {
      if (!grouped[issue.severity]) {
        grouped[issue.severity] = [];
      }
      grouped[issue.severity].push(issue);
    });
    return grouped;
  }

  getCriticalCount(): number {
    return this.currentDocument?.issues?.filter(i => i.severity === 'critical').length || 0;
  }

  getMajorCount(): number {
    return this.currentDocument?.issues?.filter(i => i.severity === 'major').length || 0;
  }

  getMinorCount(): number {
    return this.currentDocument?.issues?.filter(i => i.severity === 'minor' || i.severity === 'info').length || 0;
  }
}
