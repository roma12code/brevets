import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: false,
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  @Output() toggleSidebar = new EventEmitter<void>();
  @Output() togglePreview = new EventEmitter<void>();
  @Output() newConversation = new EventEmitter<void>();

  onToggleSidebar(): void {
    this.toggleSidebar.emit();
  }

  onTogglePreview(): void {
    this.togglePreview.emit();
  }

  onNewConversation(): void {
    this.newConversation.emit();
  }
}
