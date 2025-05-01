import { Injectable } from '@angular/core';
import {
  AdminConfirmSignUpCommand,
  CognitoIdentityProviderClient, InitiateAuthCommand,
  SignUpCommand, GetUserCommand
} from '@aws-sdk/client-cognito-identity-provider';
import config from '../../../public/stack-outputs.json';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class AuthService {

  private client: CognitoIdentityProviderClient;
  private readonly clientId: string;
  private readonly userPoolId: string;

  constructor(private router: Router) {
    this.clientId = config.CdkStack.UserPoolClientId;
    this.userPoolId = config.CdkStack.UserPoolId;
    this.client = new CognitoIdentityProviderClient({
      region: 'us-east-1',
      endpoint: config.CdkStack.APIGateway + 'cognito',
      credentials: {
        accessKeyId: 'test',
        secretAccessKey: 'test'
      }
    });
  }

  async signUp(email: string, password: string, firstName: string, lastName: string, profilePicture: string | null) {
    let command;
    if (profilePicture) {
      command = new SignUpCommand({
        ClientId: this.clientId,
        Username: email,
        Password: password,
        UserAttributes: [
          {Name: 'email', Value: email},
          {Name: 'given_name', Value: firstName},
          {Name: 'family_name', Value: lastName},
          {Name: 'picture', Value: profilePicture}
        ]
      });
    } else {
      command = new SignUpCommand({
        ClientId: this.clientId,
        Username: email,
        Password: password,
        UserAttributes: [
          {Name: 'email', Value: email},
          {Name: 'given_name', Value: firstName},
          {Name: 'family_name', Value: lastName},
        ]
      });
    }

    try {
      const response = await this.client.send(command);
      console.log('Signup successful', response);
      await this.confirmSignUp(email)
      return response;
    } catch (error) {
      console.error('Signup failed', error);
      throw error;
    }
  }

  async confirmSignUp(username: string) {
    const command = new AdminConfirmSignUpCommand({
      UserPoolId: this.userPoolId,
      Username: username
    });

    try {
      await this.client.send(command);
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('Confirmation failed', error);
      throw error;
    }
  }

  async login(username: string, password: string) {
    const command = new InitiateAuthCommand({
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: this.clientId,
      AuthParameters: {
        USERNAME: username,
        PASSWORD: password
      }
    });

    try {
      const response = await this.client.send(command);

      if (response.AuthenticationResult
        && response.AuthenticationResult.AccessToken
        && response.AuthenticationResult.IdToken
        && response.AuthenticationResult.RefreshToken) {
        localStorage.setItem('accessToken', response.AuthenticationResult.AccessToken);
        localStorage.setItem('idToken', response.AuthenticationResult.IdToken);
        localStorage.setItem('refreshToken', response.AuthenticationResult.RefreshToken);
      }

      this.router.navigate(['/']);

      return response;
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    }
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('accessToken');
  }

  logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('idToken');
    localStorage.removeItem('refreshToken');
  }

  async getUserId(): Promise<string | undefined | null> {
    const accessToken = localStorage.getItem('accessToken');
    if(accessToken) {
      const command = new GetUserCommand({
        AccessToken: accessToken,
      });
      const response = await this.client.send(command);
      const sub = response.UserAttributes?.find(attr => attr.Name === 'sub')?.Value;
      return sub || null;
    }
    return null;
  }

  async getProfilePictureName(): Promise<string | undefined | null>{
    const accessToken = localStorage.getItem('accessToken');
    if(accessToken) {
      const command = new GetUserCommand({
        AccessToken: accessToken,
      });
      const response = await this.client.send(command);
      const picture = response.UserAttributes?.find(attr => attr.Name === 'picture')?.Value;
      return picture || null;
    }
    return null;
  }
}
