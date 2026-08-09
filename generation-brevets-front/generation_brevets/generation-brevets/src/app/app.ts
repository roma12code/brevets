import { Component } from '@angular/core';
import { Brevet } from './brevet/brevet'; // ✅ Import du composant Brevet

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [Brevet], // ✅ Ajout de Brevet
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent {
  title = 'generation-brevets';
}
