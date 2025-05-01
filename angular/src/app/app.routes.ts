import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { ResultsComponent } from './components/results/results.component';
import { ExercisesComponent } from './components/exercises/exercises.component';
import { LoginComponent } from './components/login/login.component';
import { SignupComponent } from './components/signup/signup.component';

export const routes: Routes = [
  {path: '', component: HomeComponent},
  {path: 'results', component: ResultsComponent},
  {path: 'exercises', component: ExercisesComponent},
  {path: 'login', component: LoginComponent},
  {path: 'signup', component: SignupComponent},
];
