import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ComplianceReport, ConversationHistory } from '../models/models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {
    console.log('🌐 Backend URL:', this.apiUrl);
  }

  /**
   * 📤 Upload et analyse d'un PDF
   * POST /api/documents/analyze
   */
  analyzeDocument(file: File, normes: string[] = ['CONSISTANCE', 'PRECISION', 'REDACTION']): Observable<ComplianceReport> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('normes', normes.join(','));

    // Le backend retourne DÉJÀ le bon format
    return this.http.post<ComplianceReport>(
      `${this.apiUrl}/documents/analyze`,
      formData
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * 📋 Récupérer l'historique
   * GET /api/history
   */
  getAllResults(): Observable<ConversationHistory[]> {
  return this.http.get<ConversationHistory[]>(`${this.apiUrl}/history`).pipe(
    map(response => {
      // Le backend renvoie déjà le bon format, on s'assure juste que les dates sont des objets Date
      if (Array.isArray(response)) {
        return response.map(item => ({
          ...item,
          date: new Date(item.date)
        }));
      }
      return [];
    }),
    catchError(this.handleError)
  );
}

  /**
   * 📄 Récupérer un rapport spécifique
   * GET /api/reports/{report_id}
   */
  getResultById(id: string): Observable<ComplianceReport> {
    return this.http.get<ComplianceReport>(`${this.apiUrl}/reports/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * 🗑️ Supprimer un rapport
   * DELETE /api/history/{report_id}
   */
  deleteResult(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/history/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * 💬 Chat
   * POST /api/chat
   */
  sendChatMessage(message: string, conversationId?: string): Observable<{ response: string }> {
    return this.http.post<{ response: string }>(`${this.apiUrl}/chat`, {
      message,
      conversationId
    }).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * 📚 Récupérer les normes
   * GET /api/normes
   */
  getAvailableNormes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/normes`).pipe(
      catchError(this.handleError)
    );
  }

  // =================================================
  // ============= HELPERS ===========================
  // =================================================

  private transformToHistory(backend: any): ConversationHistory {
    const filename = backend?.documentName || backend?.filename || backend?.name || 'Document';
    const id = backend?.documentId || backend?.id || this.generateId();
    const score = backend?.overallScore ?? backend?.score ?? 0;
    const status = backend?.status || backend?.overall_status || 'partial';
    const timestamp = backend?.timestamp || backend?.uploadDate || backend?.date || new Date().toISOString();
    
    return {
      id: id,
      title: filename.replace(/\.(pdf|docx|txt)$/i, ''),
      lastMessage: `Score: ${score}% - ${this.getStatusLabel(status)}`,
      date: new Date(timestamp),
      documentsCount: 1,
      status: this.mapStatus(status)
    };
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  private mapStatus(status: string): 'compliant' | 'non-compliant' | 'partial' {
    const lower = (status || '').toLowerCase();
    
    switch (lower) {
      case 'compliant':
      case 'conforme':
        return 'compliant';
      case 'non-compliant':
      case 'non_conforme':
      case 'nonconforme':
        return 'non-compliant';
      case 'partial':
      case 'partiel':
        return 'partial';
      default:
        return 'partial';
    }
  }

  private getStatusLabel(status: string): string {
    const mapped = this.mapStatus(status);
    switch (mapped) {
      case 'compliant': return 'Conforme';
      case 'non-compliant': return 'Non conforme';
      case 'partial': return 'Partiel';
      default: return status;
    }
  }

  private handleError(error: any): Observable<never> {
    let errorMessage = 'Une erreur est survenue';
    
    if (error.status === 0) {
      errorMessage = '🔌 Backend indisponible. Vérifiez que le serveur Python tourne.';
    } else if (error.status === 400) {
      errorMessage = '⚠️ Requête invalide.';
    } else if (error.status === 404) {
      errorMessage = '❌ Ressource non trouvée.';
    } else if (error.status === 413) {
      errorMessage = '📦 Fichier trop volumineux.';
    } else if (error.status === 422) {
      errorMessage = '⚠️ Format des données invalide.';
    } else if (error.status === 500) {
      errorMessage = '🔥 Erreur serveur. Vérifiez la clé API Groq.';
    } else {
      errorMessage = `Erreur ${error.status}: ${error.message || 'Erreur inconnue'}`;
    }
    
    console.error('❌ API Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}