import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { HeaderMenuComponent } from '../header-menu/header-menu.component';

@Component({
  selector: 'app-login',
  imports: [
    FormsModule,
    RouterLink,
    HeaderMenuComponent
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  protected username: string | undefined;
  protected password: string | undefined;
  constructor(private auth: AuthService,
              private router: Router) {
  }

  async login() {
    if (this.username && this.password) {
      try {
        const response = await this.auth.login(this.username, this.password);

        this.router.navigate(['/']);
      } catch(error) {
        // TODO: Add proper error handling, e.g. for UserNotFoundException;
      }
    }
  }
}
