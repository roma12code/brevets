import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import {
  DocumentFile,
  ChatMessage,
  ComplianceReport,
  ConversationHistory
} from '../models/models';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class DocumentService {

  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  messages$ = this.messagesSubject.asObservable();

  private historySubject = new BehaviorSubject<ConversationHistory[]>([]);
  history$ = this.historySubject.asObservable();

  private currentDocumentSubject = new BehaviorSubject<DocumentFile | null>(null);
  currentDocument$ = this.currentDocumentSubject.asObservable();

  private selectedNormesSubject = new BehaviorSubject<string[]>(['CONSISTANCE', 'PRECISION', 'REDACTION']);
  selectedNormes$ = this.selectedNormesSubject.asObservable();

  private activeConversationId: string | null = null;

  availableNormes = [
    { 
      code: 'CONSISTANCE', 
      name: 'Consistance Inter-Section', 
      icon: '🔗',
      description: 'Cohérence entre les sections'
    },
    { 
      code: 'PRECISION', 
      name: 'Précision Technique', 
      icon: '🎯',
      description: 'Exactitude des informations techniques'
    },
    { 
      code: 'REDACTION', 
      name: 'Qualité Rédactionnelle', 
      icon: '✍️',
      description: 'Français simple et clair'
    }
  ];

constructor(private apiService: ApiService) {
  this.initWelcomeMessage();
  this.loadHistoryFromBackend();  // ⭐ Plus de checkBackendHealth
}

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Vérifie que le backend est accessible au démarrage
   */


private initWelcomeMessage(): void {
  const welcomeMessage: ChatMessage = {
    id: this.generateId(),
    type: 'bot',
    content: `👋 Bienvenue dans **NormaCheck AI** !\n\n` +
      `Je suis votre assistant intelligent pour vérifier si votre **brevet** respecte les normes de qualité requises.\n\n` +
      `📋 **L'analyse vérifie automatiquement 3 normes essentielles :**\n\n` +
      `🔗 **Consistance Inter-Section** - Cohérence entre les différentes sections du brevet\n` +
      `🎯 **Précision Technique** - Exactitude des informations techniques\n` +
      `✍️ **Qualité Rédactionnelle** - Clarté du français et lisibilité\n\n` +
      `📎 **Glissez-déposez votre brevet (PDF)** ou cliquez sur le bouton d'upload pour lancer l'analyse.\n\n` +
      `⏱️ _L'analyse prend entre 30 et 90 secondes._`,
    timestamp: new Date()
  };
  this.messagesSubject.next([welcomeMessage]);
}

  /**
   * Charge l'historique depuis le backend
   */
  loadHistoryFromBackend(): void {
    this.apiService.getAllResults().subscribe({
      next: (history) => {
        this.historySubject.next(history);
        console.log(`📋 ${history.length} analyses chargées depuis le backend`);
      },
      error: (err) => {
        console.warn('⚠️ Impossible de charger l\'historique:', err.message);
        this.historySubject.next([]);
      }
    });
  }

  /**
   * Upload et analyse un document via le backend
   */
/**
 * Upload et analyse un document via le backend
 */
uploadDocument(file: File): Observable<DocumentFile> {
  const doc: DocumentFile = {
    id: this.generateId(),
    name: file.name,
    size: file.size,
    type: file.type,
    uploadDate: new Date(),
    status: 'uploading',
    file: file
  };

  // 1. Message utilisateur
  const userMsg: ChatMessage = {
    id: this.generateId(),
    type: 'user',
    content: `📄 **Brevet envoyé pour analyse :**\n\n📎 ${file.name} (${this.formatFileSize(file.size)})`,
    timestamp: new Date(),
    attachedDocument: doc
  };

  const currentMessages = this.messagesSubject.getValue();
  this.messagesSubject.next([...currentMessages, userMsg]);

  // 2. Message bot "analyse en cours"
  doc.status = 'analyzing';
  this.addBotMessage(
    `⏳ **Analyse de votre brevet en cours...**\n\n` +
    `L'IA examine votre document selon les 3 normes de qualité :\n\n` +
    `  🔗 Consistance Inter-Section\n` +
    `  🎯 Précision Technique\n` +
    `  ✍️ Qualité Rédactionnelle\n\n` +
    `⏱️ _Cela peut prendre **30 à 90 secondes**. Merci de patienter..._`
  );

  // 3. Appel au backend (les 3 normes sont envoyées automatiquement)
  this.apiService.analyzeDocument(file).subscribe({
    next: (report: ComplianceReport) => {
      doc.status = report.status;
      doc.complianceScore = report.overallScore;
      doc.issues = report.normesCovered.flatMap(n => (n as any).issues || []);
      this.currentDocumentSubject.next(doc);
      this.addBotMessageWithReport(report);
      this.loadHistoryFromBackend();
    },
    error: (err) => {
      doc.status = 'non-compliant';
      this.addBotMessage(
        `❌ **Erreur lors de l'analyse**\n\n` +
        `${err.message}\n\n` +
        `💡 **Vérifications :**\n` +
        `• Le fichier est bien un PDF ?\n` +
        `• Le backend est démarré ?\n` +
        `• La clé API Groq est valide ?`
      );
    }
  });

  return of(doc);
}

  private addBotMessage(content: string): void {
    const msg: ChatMessage = {
      id: this.generateId(),
      type: 'bot',
      content,
      timestamp: new Date()
    };
    const current = this.messagesSubject.getValue();
    this.messagesSubject.next([...current, msg]);
  }

private addBotMessageWithReport(report: ComplianceReport): void {
  const statusEmoji = report.status === 'compliant' ? '✅' : report.status === 'partial' ? '⚠️' : '❌';
  const statusText = report.status === 'compliant' ? 'Brevet Conforme' : report.status === 'partial' ? 'Brevet Partiellement Conforme' : 'Brevet Non Conforme';

  let content = `## ${statusEmoji} Résultat de l'Analyse\n\n`;
  content += `**📄 Document :** ${report.documentName}\n`;
  content += `**📊 Score global :** ${report.overallScore}%\n`;
  content += `**🎯 Verdict :** ${statusText}\n\n`;
  content += `### 📋 Détail par norme :\n\n`;

  report.normesCovered.forEach(norme => {
    const icon = norme.passed ? '✅' : norme.score >= 60 ? '⚠️' : '❌';
    const normeInfo = this.availableNormes.find(n => n.code === norme.normeCode);
    const displayName = normeInfo ? `${normeInfo.icon} ${normeInfo.name}` : norme.normeName;
    content += `${icon} **${displayName}** — ${norme.score}/100\n\n`;
  });

  if (report.totalIssues > 0) {
    content += `### 🔍 ${report.totalIssues} point(s) à améliorer détecté(s)\n\n`;
  } else {
    content += `### 🎉 Aucun problème détecté !\n\n`;
  }
  
  content += `> ${report.summary}\n\n`;
  content += `_💡 Cliquez sur **Rapport** à droite pour voir les recommandations détaillées._`;

  const msg: ChatMessage = {
    id: this.generateId(),
    type: 'bot',
    content,
    timestamp: new Date(),
    complianceReport: report
  };
  const current = this.messagesSubject.getValue();
  this.messagesSubject.next([...current, msg]);
}
  sendMessage(content: string): void {
    const userMsg: ChatMessage = {
      id: this.generateId(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    const current = this.messagesSubject.getValue();
    this.messagesSubject.next([...current, userMsg]);

    // Réponse locale (pas d'endpoint /chat dans le backend actuel)
    setTimeout(() => {
      this.generateLocalResponse(content);
    }, 500);
  }

  private generateLocalResponse(userMessage: string): void {
    const lowerMsg = userMessage.toLowerCase();
    let response = '';

    if (lowerMsg.includes('norme')) {
      response = `📋 **Normes analysées :**\n\n`;
      this.availableNormes.forEach(n => {
        response += `${n.icon} **${n.name}** — ${n.description}\n`;
      });
    } else if (lowerMsg.includes('aide') || lowerMsg.includes('help') || lowerMsg.includes('comment')) {
      response = `🤖 **Comment utiliser NormaCheck AI :**\n\n` +
        `1. 📎 Uploadez un document **PDF**\n` +
        `2. ⏳ Patientez **30 à 90 secondes** pendant l'analyse IA\n` +
        `3. 📊 Consultez le rapport détaillé\n` +
        `4. 💡 Suivez les recommandations d'amélioration\n\n` +
        `📜 L'historique de vos analyses est disponible dans la sidebar à gauche.`;
    } else if (lowerMsg.includes('rapport') || lowerMsg.includes('résultat')) {
      const currentDoc = this.currentDocumentSubject.getValue();
      if (currentDoc) {
        response = `📄 **Dernier document :** ${currentDoc.name}\n\n` +
          `Score : **${currentDoc.complianceScore || 'N/A'}%**\n\n` +
          `Consultez le panneau de droite pour le détail.`;
      } else {
        response = `📭 Aucun document analysé pour le moment.\n\nUploadez un PDF pour commencer !`;
      }
    } else {
      response = `🤖 Je suis votre assistant d'analyse documentaire.\n\n` +
        `Pour commencer, **uploadez un document PDF** en cliquant sur 📎 ou en le glissant ici.\n\n` +
        `Vous pouvez aussi me demander :\n` +
        `• "Quelles sont les normes ?"\n` +
        `• "Comment ça marche ?"\n` +
        `• "Montre-moi le dernier rapport"`;
    }

    this.addBotMessage(response);
  }

  setSelectedNormes(normes: string[]): void {
    this.selectedNormesSubject.next(normes);
  }

  newConversation(): void {
    this.activeConversationId = this.generateId();
    this.currentDocumentSubject.next(null);
    this.initWelcomeMessage();
  }

  loadConversation(id: string): void {
    this.activeConversationId = id;
    this.apiService.getResultById(id).subscribe({
      next: (report) => {
        this.addBotMessage(`📂 **Conversation chargée** : ${report.documentName}`);
        this.addBotMessageWithReport(report);
        
        // Mettre à jour le document courant
        const doc: DocumentFile = {
          id: report.documentId,
          name: report.documentName,
          size: 0,
          type: 'application/pdf',
          uploadDate: new Date(),
          status: report.status,
          complianceScore: report.overallScore,
          issues: report.normesCovered.flatMap(n => (n as any).issues || [])
        };
        this.currentDocumentSubject.next(doc);
      },
      error: (err) => {
        this.addBotMessage(`❌ Impossible de charger cette conversation.\n\n${err.message}`);
      }
    });
  }

  deleteConversation(id: string): void {
    this.apiService.deleteResult(id).subscribe({
      next: () => {
        const current = this.historySubject.getValue();
        this.historySubject.next(current.filter(h => h.id !== id));
        console.log('✅ Conversation supprimée');
      },
      error: (err) => {
        console.error('❌ Erreur suppression:', err);
      }
    });
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
