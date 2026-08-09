import { Component } from '@angular/core';
import { DocumentService } from './services/document.service';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  isSidebarOpen = false;
  isPreviewOpen = false;

  constructor(private documentService: DocumentService) {}

  toggleSidebar(): void {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  togglePreview(): void {
    this.isPreviewOpen = !this.isPreviewOpen;
  }

  closeSidebar(): void {
    this.isSidebarOpen = false;
  }

  closePreview(): void {
    this.isPreviewOpen = false;
  }

  onNewConversation(): void {
    this.documentService.newConversation();
    this.isSidebarOpen = false;
  }

  onConversationSelected(id: string): void {
    this.documentService.loadConversation(id);
    this.isSidebarOpen = false;
  }
}
