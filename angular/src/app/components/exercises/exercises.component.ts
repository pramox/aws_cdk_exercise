import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HeaderMenuComponent } from "../header-menu/header-menu.component";

@Component({
  selector: 'app-exercises',
    imports: [CommonModule, ReactiveFormsModule, HeaderMenuComponent, RouterLink],
  templateUrl: './exercises.component.html',
  styleUrl: './exercises.component.css',
  standalone: true
})
export class ExercisesComponent implements OnInit {
  exerciseForm: FormGroup;
  currentExercise: any = null;
  showButtons: boolean = true;
  userId: string = '';
  displayQuestion: string = '';

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    protected router: Router,
    protected authService: AuthService
  ) {
    this.exerciseForm = this.fb.group({
      userAnswer: [''],
    });
  }

  async ngOnInit(): Promise<void> {
    const sub = await this.authService.getUserId();
    if (typeof sub === 'string') {
      this.userId = sub;
    } else {
      console.error('Failed to retrieve User ID');
    }
  }

  fetchExercise(topic: string): void {
    console.log('Fetching exercise with:', this.userId, topic);
    this.apiService.getExercise(this.userId, topic).subscribe({
      next: (exercise) => {
        exercise = JSON.parse(exercise)
        this.currentExercise = exercise;
        this.displayQuestion = this.formatQuestion(
          exercise.Question,
          exercise.ExerciseType
        );
        this.showButtons = false;
      },
      error: (err) => {
        console.error('Error fetching exercise:', err);
        const errorMessage = err.error?.error || 'Error fetching results.';
        alert(`Error: ${errorMessage}`);
      },
    });
  }

  formatQuestion(rawQuestion: string, exerciseType: string): string{
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

  submitSolution(): void {
    const payload = {
      user_id: this.userId,
      exercise_id: this.currentExercise.SK,
      topic: this.currentExercise.ExerciseType,
      user_answer: this.formatAnswerForBackend(
        this.exerciseForm.value.userAnswer,
        this.currentExercise.ExerciseType
      ),
    };

    this.apiService.postSolution(payload).subscribe({
      next: () => {
        this.currentExercise = null;
        this.displayQuestion = '';
        this.exerciseForm.reset();
        this.showButtons = true;
      },
      error: (err) => {
        console.error('Error submitting solution:', err);
        const errorMessage = err.error?.error || 'Error submitting solution.';
        alert(`Error: ${errorMessage}`);
      },
    });
  }

  formatAnswerForBackend(userAnswer: string, exerciseType: string): string {
    if (exerciseType === 'DERIVATIVE') {
      return userAnswer.split('+').map((term) => {
          term = term.trim();
          const match = term.match(/(\d+)(x\^(\d+)|x)?/);
          if (!match) return term;
          const coefficient = match[1];
          const exponent = match[3] || (match[2] ? '1' : '0');
          return `${coefficient}:${exponent}`;
        })
        .join(',');
    }
    return userAnswer;
  }
}
