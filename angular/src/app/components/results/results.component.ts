import {Component} from '@angular/core';
import {ApiService} from '../../services/api.service';
import {CommonModule} from '@angular/common';
import {AuthService} from '../../services/auth.service';
import {Router, RouterLink} from '@angular/router';
import {HeaderMenuComponent} from '../header-menu/header-menu.component';
import {Result} from './result.model';

@Component({
  selector: 'app-results',
  imports: [CommonModule, HeaderMenuComponent, RouterLink],
  templateUrl: './results.component.html',
  styleUrl: './results.component.css',
  standalone: true
})
export class ResultsComponent {
  results: Result[] = [];
  userId: string | undefined;

  constructor(private apiService: ApiService, protected authService: AuthService, protected router: Router) {
  }

  async ngOnInit(): Promise<void> {
    const sub = await this.authService.getUserId();
    if (typeof sub === 'string') {
      this.userId = sub;
      this.fetchResults();
    } else {
      console.error('Failed to retrieve User ID');
    }
  }

  fetchResults(): void {
    console.log('Fetching results with id :', this.userId);
    if (!this.userId) return;
    this.apiService.getResults(this.userId).subscribe({
      next: (response) => {
        console.log('Results:', response);
        const sanitizedJsonString = response.results.replace(/Decimal\('(.*?)'\)/g, '$1');
        const updatedString = sanitizedJsonString.replace(/False/g, '"False"');
        const updatedString1 = updatedString.replace(/True/g, '"True"');
        this.results = JSON.parse(updatedString1.replace(/'/g, '"'));
        console.log("results", this.results);
      },
      error: (err) => {
        console.error('Error fetching results:', err);
        const errorMessage = err.error?.error || 'Error fetching results.';
        alert(`Error: ${errorMessage}`);
      },
    });
  }

  formatQuestion(rawQuestion: string, exerciseType: string): string {
    if (exerciseType === 'ADDITION') {
      return rawQuestion.split(',').join(' + ');
    } else if (exerciseType === 'MULTIPLICATION') {
      return rawQuestion.split(',').join(' * ');
    } else if (exerciseType === 'DERIVATIVE') {
      const terms = rawQuestion.split(',');
      return terms.map((term) => {
        const [coefficient, exponent] = term.split(':');
        if (parseInt(exponent, 10) === 0) return coefficient;
        if (parseInt(exponent, 10) === 1) return `${coefficient}x`;
        return `${coefficient}x^${exponent}`;
      }).join(' + ');
    } else {
      return rawQuestion;
    }
  }

  calculateGrade(): number {
    const ratio = this.countCorrect() / this.countSolved();
    if (ratio > 0.87) return 1;
    if (ratio > 0.74) return 2;
    if (ratio > 0.59) return 3;
    if (ratio > 0.49) return 4;
    return 5;
  }

  countSolved(): number {
    var count = 0;
    for (let result of this.results) {
      if (result.IsSolved) {
        count++;
      }
    }
    return count;
  }

  countCorrect(): number {
    var correct = 0;
    for (let result of this.results) {
      if (result.IsCorrect === "True") {
        correct++;
      }
    }
    return correct;
  }

}
