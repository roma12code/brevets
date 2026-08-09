import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { DocumentService } from '../../services/document.service';
import { ChatMessage } from '../../models/models';

@Component({
  selector: 'app-chat-area',
  standalone: false,
  templateUrl: './chat-area.component.html',
  styleUrls: ['./chat-area.component.css']
})
export class ChatAreaComponent implements OnInit, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild('fileInput') private fileInput!: ElementRef;

  messages: ChatMessage[] = [];
  userInput = '';
  isDragOver = false;
  isUploading = false;
  selectedNormes: string[] = [];

  constructor(public documentService: DocumentService) {}

  ngOnInit(): void {
    this.documentService.messages$.subscribe(msgs => {
      this.messages = msgs;
    });
    this.documentService.selectedNormes$.subscribe(normes => {
      this.selectedNormes = normes;
    });
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer) {
        this.messagesContainer.nativeElement.scrollTop =
          this.messagesContainer.nativeElement.scrollHeight;
      }
    } catch (err) {}
  }

  sendMessage(): void {
    if (!this.userInput.trim()) return;
    this.documentService.sendMessage(this.userInput.trim());
    this.userInput = '';
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  triggerFileUpload(): void {
    this.fileInput.nativeElement.click();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.uploadFile(input.files[0]);
      input.value = '';
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.uploadFile(event.dataTransfer.files[0]);
    }
  }

  private uploadFile(file: File): void {
  // ⭐ Vérifier UNIQUEMENT PDF
  if (file.type !== 'application/pdf') {
    this.documentService.sendMessage(
      `⚠️ Format non supporté : ${file.type}\n\nSeuls les fichiers **PDF** sont acceptés par le backend.`
    );
    return;
  }

  if (file.size > 50 * 1024 * 1024) {
    this.documentService.sendMessage('⚠️ Le fichier dépasse 50 MB.');
    return;
  }

  this.isUploading = true;
  this.documentService.uploadDocument(file).subscribe({
    next: () => {
      // Le statut sera mis à jour quand l'analyse sera terminée
      // On garde isUploading à true pendant l'analyse (30-90s)
    },
    error: () => {
      this.isUploading = false;
    }
  });

  // Désactiver le loader après un délai max
  setTimeout(() => {
    this.isUploading = false;
  }, 120000); // 2 minutes max
}

  formatMessageContent(content: string): string {
    // Simple markdown-like formatting
    let formatted = content;

    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic
    formatted = formatted.replace(/_(.*?)_/g, '<em>$1</em>');

    // Headers
    formatted = formatted.replace(/^### (.*$)/gm, '<h4 class="msg-h4">$1</h4>');
    formatted = formatted.replace(/^## (.*$)/gm, '<h3 class="msg-h3">$1</h3>');

    // Blockquote
    formatted = formatted.replace(/^> (.*$)/gm, '<blockquote class="msg-quote">$1</blockquote>');

    // List items
    formatted = formatted.replace(/^- (.*$)/gm, '<div class="msg-list-item">• $1</div>');
    formatted = formatted.replace(/^  • (.*$)/gm, '<div class="msg-list-item indent">• $1</div>');

    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
  }

  getMessageTimeFormatted(date: Date): string {
    return new Date(date).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  getScoreClass(score: number | undefined): string {
    if (!score) return '';
    if (score >= 90) return 'score-high';
    if (score >= 70) return 'score-medium';
    return 'score-low';
  }
  // Ajoutez dans chat-area.component.ts
trackByMsgId(index: number, item: ChatMessage): string {
  return item.id;
}
}
