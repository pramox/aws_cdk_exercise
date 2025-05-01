import { Component } from '@angular/core';
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { HeaderMenuComponent } from '../header-menu/header-menu.component';

@Component({
  selector: 'app-signup',
  imports: [
    FormsModule,
    RouterLink,
    HeaderMenuComponent
  ],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.css'
})
export class SignupComponent {
  protected email: string | undefined;
  protected password: string | undefined;
  protected firstName: string | undefined;
  protected lastName: string | undefined;
  protected selectedFile: File | undefined;

  constructor(protected auth: AuthService, protected apiService: ApiService) {
  }

  onFileSelected(event: Event): void {
    const fileInput = event.target as HTMLInputElement;
    if (fileInput.files && fileInput.files.length > 0) {
      this.selectedFile = fileInput.files[0];
    }
  }

  signup() {
    if (this.email && this.password && this.firstName && this.lastName) {
      try {
        if (this.selectedFile) {
          const response =
            this.auth.signUp(this.email, this.password, this.firstName, this.lastName, this.selectedFile.name);
        } else {
          const response =
            this.auth.signUp(this.email, this.password, this.firstName, this.lastName, null);
        }
      } catch(error) {
        console.log(error);
      }
    }
    if (this.selectedFile) {
      this.apiService.uploadProfileImage(this.selectedFile);
    }
  }
}
