import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs';
import {map} from 'rxjs/operators';
import config from '../../../public/stack-outputs.json';
import {Result} from '../components/results/result.model';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private baseUrl: string = config.CdkStack.APIGateway;

  constructor(private http: HttpClient) {
  }

  getResults(userId: string): Observable<any> {
  const params = new HttpParams().set('user_id', userId);
  return this.http.get<any>(`${this.baseUrl}results`, { params });
}

  getExercise(userId: string, topic: string): Observable<any> {
    const params = new HttpParams().set('user_id', userId).set('topic', topic);
    return this.http.get<{ exercise: any }>(`${this.baseUrl}exercise`, {params}).pipe(
      map((response) => response.exercise)
    );
  }

  postSolution(payload: {
    user_id: string;
    exercise_id: string;
    topic: string;
    user_answer: string;
  }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}exercise`, payload);
  }

  uploadProfileImage(file: File) {
    return this.http.put<any>(`${this.baseUrl}profile-picture/${file.name}`, file).subscribe({
      next: value => {
        console.log(value);
      },
      error: error => {
        console.log(error);
      }
    });
  }

  getProfileImage(file: string) {
    return this.http.get(`${this.baseUrl}profile-picture/${file}`, { responseType: 'blob'});
  }
}
