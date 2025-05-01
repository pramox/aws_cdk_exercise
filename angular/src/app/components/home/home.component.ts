import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { HeaderMenuComponent } from '../header-menu/header-menu.component';

@Component({
  selector: 'app-home',
  imports: [RouterLink, HeaderMenuComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
  standalone: true
})
export class HomeComponent {

}
