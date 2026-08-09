import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { provideHttpClient } from '@angular/common/http';

import { AppComponent } from './app.component';
import { HeaderComponent } from './components/header/header.component';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { ChatAreaComponent } from './components/chat-area/chat-area.component';
import { DocumentPreviewComponent } from './components/document-preview/document-preview.component';
import { DocumentService } from './services/document.service';


@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    SidebarComponent,
    ChatAreaComponent,
    DocumentPreviewComponent
  ],
  imports: [
    BrowserModule,
    FormsModule
  ],
   providers: [
    DocumentService,
    provideHttpClient()  // ⭐ AJOUTER ICI
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }