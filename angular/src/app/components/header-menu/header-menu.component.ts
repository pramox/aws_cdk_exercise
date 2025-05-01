import { ChangeDetectorRef, Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import {NgIf} from '@angular/common';
import {AuthService} from '../../services/auth.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-header-menu',
  imports: [
    RouterLink,
    NgIf
  ],
  templateUrl: './header-menu.component.html',
  styleUrl: './header-menu.component.css'
})
export class HeaderMenuComponent {
  protected profileImage: string | undefined;

  constructor(protected auth: AuthService,
              protected router: Router,
              protected api: ApiService,
              private cdr: ChangeDetectorRef) {
    this.fetchProfilePicture();
  }

  async fetchProfilePicture() {
    const pictureName = await this.auth.getProfilePictureName();
    if (pictureName) {
      this.api.getProfileImage(pictureName).subscribe({
        next: value => {
          this.profileImage = URL.createObjectURL(value);
        },
        error: error => {
          console.log(error);
        }
      });
    }
  }

  logout() {
    this.auth.logout();
    this.profileImage = undefined;
    this.router.navigate(['/']);
  }
}
