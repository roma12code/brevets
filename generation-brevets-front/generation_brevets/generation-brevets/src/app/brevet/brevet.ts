import { Component, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import html2pdf from 'html2pdf.js';

interface BrevetArchive {
  id: string;
  titre: string;
  type: 'invention' | 'certificat' | 'modele';
  date: string;
  contenu: string;
}

// ── Interfaces pour les résultats d'antériorité ──
interface DocumentSimilaire {
  rang: number;
  titre: string;
  proprietaire: string;
  annee: string;
  similarite: number;
  type: string;
}

interface ResultatAnteriorite {
  verdict: 'nouveau' | 'partiel' | 'existant';
  risque: 'FAIBLE' | 'MOYEN' | 'ÉLEVÉ';
  analyse: string;
  differentiation: string;
  brevetabilite: string;
  recommandations: string;
  conclusion: string;
  documentsProches: DocumentSimilaire[];
}

@Component({
  selector: 'app-brevet',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './brevet.html',
  styleUrls: ['./brevet.css']
})
export class Brevet {
  // Champs du formulaire
  titreInvention = '';
  nomInventeur = '';
  domaineMedical = '';
  probleme = '';
  solution = '';
  description = '';
  testsCliniques = '';
  revendications = '';

  // Gestion image
  fichierSchema: File | null = null;
  imagePreview: string | null = null;

  // ── Template ──
  showTemplateModal = false;
  templateSelectionne: 'invention' | 'certificat' | 'modele' = 'invention';
  templateActif: 'invention' | 'certificat' | 'modele' = 'invention';

  // ── Mes Brevets ──
  showMesBrevetsModal = false;
  archives: BrevetArchive[] = [];
  brevetSelectionne: BrevetArchive | null = null;

  // ── Analyse d'antériorité ──
  showResultatModal = false;
  isLoading = false;
  resultatAnteriorite: ResultatAnteriorite | null = null;
  erreurAnalyse: string | null = null;

constructor(private cdr: ChangeDetectorRef) {
  this.chargerArchives();
}

  // ── Template modal ──
  ouvrirTemplateModal() {
    this.templateSelectionne = this.templateActif;
    this.showTemplateModal = true;
  }

  confirmerTemplate() {
    this.templateActif = this.templateSelectionne;
    this.showTemplateModal = false;
  }

  fermerModal() {
    this.showTemplateModal = false;
  }

  // ── Upload image ──
  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.fichierSchema = file;
      this.imagePreview = URL.createObjectURL(file);
    }
  }

  // ── Vérifier l'antériorité ──
  async onVerifier() {
  if (!this.titreInvention.trim() && !this.probleme.trim() && !this.solution.trim()) {
    alert('⚠️ Veuillez remplir au moins le titre, le problème ou la solution avant de vérifier.');
    return;
  }

  this.isLoading = true;
  this.resultatAnteriorite = null;
  this.erreurAnalyse = null;
  this.showResultatModal = true;

  try {
    const ideeTexte = this.construireTexteIdee();

    console.log('📤 Envoi de la requête...');
    console.log('Data:', {
      titre: this.titreInvention,
      domaine: this.domaineMedical,
      idee: ideeTexte,
      type_brevet: this.templateActif
    });

    const response = await fetch('http://localhost:8002/prior-art', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        idee: ideeTexte,
        titre: this.titreInvention,
        domaine: this.domaineMedical,
        type_brevet: this.templateActif
      })
    });

    console.log('📥 Réponse reçue, status:', response.status);
    console.log('Content-Type:', response.headers.get('content-type'));

    if (!response.ok) {
      throw new Error(`Erreur serveur : ${response.status}`);
    }

    const data = await response.json();
    console.log('📦 Data reçue:', data);
    console.log('✅ Success?', data.success);
    console.log('⚖️ Verdict:', data.verdict);
    console.log('📊 Documents:', data.documents_similaires?.length);

    // ⭐ Conversion avec catch d'erreur
    try {
      this.resultatAnteriorite = this.parseResultat(data);
      console.log('🎯 Résultat après parse:', this.resultatAnteriorite);
    } catch (parseError) {
      console.error('❌ ERREUR DANS parseResultat:', parseError);
      this.erreurAnalyse = 'Erreur de conversion: ' + (parseError as any).message;
    }

  } catch (error: any) {
    console.error('❌ Erreur analyse:', error);
    this.erreurAnalyse = error.message || 'Impossible de contacter le serveur.';
  }  finally {
  this.isLoading = false;
  this.cdr.detectChanges();  // ⭐ FORCE L'AFFICHAGE
}
}

  // ── Construction du texte de l'idée à analyser ──
  construireTexteIdee(): string {
    const parties = [];
    if (this.titreInvention) parties.push(`Titre: ${this.titreInvention}`);
    if (this.domaineMedical) parties.push(`Domaine: ${this.domaineMedical}`);
    if (this.probleme) parties.push(`Problème résolu: ${this.probleme}`);
    if (this.solution) parties.push(`Solution proposée: ${this.solution}`);
    if (this.description) parties.push(`Description: ${this.description}`);
    if (this.revendications) parties.push(`Revendications: ${this.revendications}`);
    return parties.join('\n\n');
  }


// ── Parse la réponse du backend (ADAPTÉE À TON API) ──
parseResultat(data: any): ResultatAnteriorite {
  // ⭐ Mapper le code du verdict (MAJUSCULES → minuscules)
  const verdictMapping: Record<string, 'nouveau' | 'partiel' | 'existant'> = {
    'IDEE_NOUVELLE': 'nouveau',
    'IDEE_PARTIELLEMENT_EXISTANTE': 'partiel',
    'IDEE_EXISTANTE': 'existant'
  };

  const verdictCode = data.verdict?.code || 'IDEE_PARTIELLEMENT_EXISTANTE';
  const verdict = verdictMapping[verdictCode] || 'partiel';

  // ⭐ Extraire l'analyse complète et la découper en sections
  const analyseComplete = data.analyse_complete || '';
  const sections = this.extraireSections(analyseComplete);

  // ⭐ Adapter les documents similaires (API → Interface Angular)
  const documentsProches: DocumentSimilaire[] = (data.documents_similaires || []).map((doc: any) => ({
    rang: doc.rang || 0,
    titre: doc.titre || 'Sans titre',
    proprietaire: doc.assignee || 'Inconnu',
    annee: doc.year || 'N/A',
    similarite: doc.similarite || 0,
    type: doc.type_document || 'Document'
  }));

  return {
    verdict: verdict,
    risque: data.verdict?.niveau_risque || 'MOYEN',
    analyse: sections['analyse'] || data.verdict?.explication || 'Aucune analyse disponible',
    differentiation: sections['differentiation'] || 'Aucune information de différenciation',
    brevetabilite: sections['brevetabilite'] || 'Aucune analyse de brevetabilité',
    recommandations: sections['recommandations'] || data.verdict?.recommandation || 'Aucune recommandation',
    conclusion: sections['conclusion']|| 'Aucune conclusion disponible',
    documentsProches: documentsProches
  };
}

// ⭐ NOUVELLE FONCTION : Extraire les sections du Markdown du LLM
extraireSections(analyseComplete: string): Record<string, string> {
  const sections: Record<string, string> = {
    analyse: '',
    differentiation: '',
    brevetabilite: '',
    recommandations: '',
    conclusion: ''
  };

  if (!analyseComplete) return sections;

  const lines = analyseComplete.split('\n');
  let currentSection = '';
  let currentContent: string[] = [];

  for (const line of lines) {
    const lineLower = line.toLowerCase();
    
    if (lineLower.includes('analyse d\'antériorité') || lineLower.includes('1. analyse')) {
      if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
      currentSection = 'analyse';
      currentContent = [];
    } else if (lineLower.includes('différenciation') || lineLower.includes('2. différenciation')) {
      if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
      currentSection = 'differentiation';
      currentContent = [];
    } else if (lineLower.includes('brevetabilité') || lineLower.includes('3. analyse de brevetabilité')) {
      if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
      currentSection = 'brevetabilite';
      currentContent = [];
    } else if (lineLower.includes('recommandations') || lineLower.includes('4. recommandations')) {
      if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
      currentSection = 'recommandations';
      currentContent = [];
    } else if (lineLower.includes('conclusion') || lineLower.includes('5. conclusion')) {
      if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
      currentSection = 'conclusion';
      currentContent = [];
    } else if (currentSection) {
      currentContent.push(line);
    }
  }

  if (currentSection) {
    sections[currentSection] = currentContent.join('\n').trim();
  }

  return sections;
}

  // ── Fermer le modal de résultat ──
  fermerResultatModal() {
    this.showResultatModal = false;
  }

  // ── Getters pour l'affichage du verdict ──
  get verdictLabel(): string {
    if (!this.resultatAnteriorite) return '';
    const labels: Record<string, string> = {
      nouveau: '✅ Idée potentiellement nouvelle',
      partiel: '⚠️ Idée partiellement existante',
      existant: '❌ Idée probablement déjà brevetée'
    };
    return labels[this.resultatAnteriorite.verdict] || '';
  }

  get verdictClass(): string {
    if (!this.resultatAnteriorite) return '';
    const classes: Record<string, string> = {
      nouveau: 'verdict-nouveau',
      partiel: 'verdict-partiel',
      existant: 'verdict-existant'
    };
    return classes[this.resultatAnteriorite.verdict] || '';
  }

  get risqueClass(): string {
    if (!this.resultatAnteriorite) return '';
    const classes: Record<string, string> = {
      'FAIBLE': 'risque-faible',
      'MOYEN': 'risque-moyen',
      'ÉLEVÉ': 'risque-eleve'
    };
    return classes[this.resultatAnteriorite.risque] || '';
  }

  getSimilariteClass(score: number): string {
    if (score >= 80) return 'sim-haute';
    if (score >= 60) return 'sim-moyenne';
    return 'sim-basse';
  }

  // ── Télécharger + Sauvegarder ──
  onTelecharger() {
    const element = document.querySelector('.panel.right .content') as HTMLElement;
    if (!element) return;

    const options: any = {
      margin: 0.5,
      filename: `brevet_${this.titreInvention || 'sans-titre'}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(options).from(element).save();

    this.sauvegarderDansArchive(element.innerHTML);
  }

  // ── Sauvegarde avec conversion blob → base64 ──
  sauvegarderDansArchive(htmlContenu: string) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContenu;
    const img = tempDiv.querySelector('img');

    if (img) {
      img.style.cssText = `
        display: block !important;
        max-width: 220px !important;
        max-height: 180px !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        margin-top: 10px;
        border: 1px solid #ccc;
        border-radius: 8px;
      `;
    }

    const sauvegarder = (contenuFinal: string) => {
      const now = new Date();
      const dateStr = now.toLocaleDateString('fr-FR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });

      const nouveau: BrevetArchive = {
        id: Date.now().toString(),
        titre: this.titreInvention || 'Sans titre',
        type: this.templateActif,
        date: dateStr,
        contenu: contenuFinal
      };

      this.archives.unshift(nouveau);
      localStorage.setItem('brevets_archives', JSON.stringify(this.archives));
    };

    if (img && img.src.startsWith('blob:')) {
      fetch(img.src)
        .then(r => r.blob())
        .then(blob => new Promise<string>((res, rej) => {
          const reader = new FileReader();
          reader.onload = () => res(reader.result as string);
          reader.onerror = rej;
          reader.readAsDataURL(blob);
        }))
        .then(base64 => {
          img.src = base64;
          sauvegarder(tempDiv.innerHTML);
        })
        .catch(() => {
          sauvegarder(tempDiv.innerHTML);
        });
    } else {
      sauvegarder(htmlContenu);
    }
  }

  chargerArchives() {
    const data = localStorage.getItem('brevets_archives');
    if (data) {
      this.archives = JSON.parse(data);
    }
  }

  supprimerBrevet(id: string) {
    this.archives = this.archives.filter(b => b.id !== id);
    localStorage.setItem('brevets_archives', JSON.stringify(this.archives));
  }

  // ── Mes Brevets modal ──
  ouvrirMesBrevets() {
    this.chargerArchives();
    this.brevetSelectionne = null;
    this.showMesBrevetsModal = true;
  }

  fermerMesBrevets() {
    this.showMesBrevetsModal = false;
    this.brevetSelectionne = null;
  }

  voirBrevet(b: BrevetArchive) {
    this.brevetSelectionne = b;
  }

  telechargerBrevetArchive(b: BrevetArchive) {
    const div = document.createElement('div');
    div.innerHTML = b.contenu;
    div.style.padding = '20px';
    document.body.appendChild(div);

    const options: any = {
      margin: 0.5,
      filename: `brevet_${b.titre}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(options).from(div).save().then(() => {
      document.body.removeChild(div);
    });
  }

  typeLabel(type: string): string {
    const labels: Record<string, string> = {
      invention: "Brevet d'invention",
      certificat: "Certificat d'utilité",
      modele: "Modèle industriel"
    };
    return labels[type] || type;
  }

  typeEmoji(type: string): string {
    const emojis: Record<string, string> = {
      invention: '📋',
      certificat: '📜',
      modele: '🏭'
    };
    return emojis[type] || '📄';
  }
}