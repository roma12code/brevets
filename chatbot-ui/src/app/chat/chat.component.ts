// src/app/chat/chat.component.ts
import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  AfterViewChecked,
  ChangeDetectorRef,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from './chat.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [DatePipe, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

  messages: ChatMessage[] = [];
  userInput = '';
  isLoading = false;
  private shouldScroll = false;

  suggestedQuestions = [
    "Qu'est-ce qu'un brevet d'invention ?",
    "Comment protéger une marque commerciale ?",
    "Quelle est la durée d'un droit d'auteur ?",
    "Différence entre brevet et droit d'auteur ?",
  ];

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.addWelcomeMessage();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private addWelcomeMessage(): void {
    this.messages.push({
      role: 'bot',
      content: "Bonjour ! Je suis votre assistant expert en **propriété intellectuelle**. Je peux répondre à vos questions sur les brevets, marques, droits d'auteur et bien plus encore. Comment puis-je vous aider ?",
      timestamp: new Date(),
    });
  }

  sendMessage(): void {
    const question = this.userInput.trim();
    if (!question || this.isLoading) return;

    this.messages = [...this.messages, {
      role: 'user',
      content: question,
      timestamp: new Date(),
    }];

    this.userInput = '';
    this.isLoading = true;
    this.shouldScroll = true;
    this.cdr.detectChanges();

    const loadingMsg: ChatMessage = {
      role: 'bot',
      content: '',
      timestamp: new Date(),
      loading: true,
    };

    this.messages = [...this.messages, loadingMsg];
    this.cdr.detectChanges();

    this.chatService.sendQuestion(question).subscribe({
      next: (response) => {
        this.messages = this.messages.map(m =>
          m === loadingMsg
            ? { role: 'bot', content: response.answer, timestamp: new Date(), loading: false }
            : m
        );
        this.isLoading = false;
        this.shouldScroll = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.messages = this.messages.map(m =>
          m === loadingMsg
            ? { role: 'bot', content: '⚠️ Une erreur est survenue. Vérifiez que le serveur backend est démarré sur le port 8000.', timestamp: new Date(), loading: false }
            : m
        );
        this.isLoading = false;
        this.shouldScroll = true;
        this.cdr.detectChanges();
      },
    });
  }

  useSuggestion(question: string): void {
    this.userInput = question;
    this.sendMessage();
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  clearChat(): void {
    this.messages = [];
    this.addWelcomeMessage();
    this.cdr.detectChanges();
  }

  private scrollToBottom(): void {
    try {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch {}
  }

  formatContent(content: string): string {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .replace(/\n/g, '<br>');
  }

  get showSuggestions(): boolean {
    return this.messages.length <= 1;
  }
}