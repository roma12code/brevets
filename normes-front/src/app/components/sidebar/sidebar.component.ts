import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { DocumentService } from '../../services/document.service';
import { ConversationHistory } from '../../models/models';

@Component({
  selector: 'app-sidebar',
  standalone: false,
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit {
  @Input() isOpen = true;
  @Output() closeSidebar = new EventEmitter<void>();
  @Output() conversationSelected = new EventEmitter<string>();

  history: ConversationHistory[] = [];
  searchTerm = '';
  filteredHistory: ConversationHistory[] = [];

  constructor(private documentService: DocumentService) {}

  ngOnInit(): void {
    this.documentService.history$.subscribe(h => {
      this.history = h;
      this.filterHistory();
    });
  }

  filterHistory(): void {
    if (!this.searchTerm.trim()) {
      this.filteredHistory = this.history;
    } else {
      this.filteredHistory = this.history.filter(h =>
        h.title.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        h.lastMessage.toLowerCase().includes(this.searchTerm.toLowerCase())
      );
    }
  }

  onSearch(): void {
    this.filterHistory();
  }

  selectConversation(id: string): void {
    this.conversationSelected.emit(id);
  }

  deleteConversation(event: Event, id: string): void {
    event.stopPropagation();
    this.documentService.deleteConversation(id);
  }

  newConversation(): void {
    this.documentService.newConversation();
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'compliant': return 'status-compliant';
      case 'non-compliant': return 'status-non-compliant';
      case 'partial': return 'status-partial';
      default: return 'status-pending';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'compliant': return '✅';
      case 'non-compliant': return '❌';
      case 'partial': return '⚠️';
      default: return '⏳';
    }
  }

  formatDate(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (hours < 1) return 'Il y a quelques minutes';
    if (hours < 24) return `Il y a ${hours}h`;
    if (days < 7) return `Il y a ${days}j`;
    return new Date(date).toLocaleDateString('fr-FR');
  }

  close(): void {
    this.closeSidebar.emit();
  }
  // Ajoutez dans sidebar.component.ts
getCompliantCount(): number {
  return this.history.filter(h => h.status === 'compliant').length;
}

trackByFn(index: number, item: ConversationHistory): string {
  return item.id;
}
}
