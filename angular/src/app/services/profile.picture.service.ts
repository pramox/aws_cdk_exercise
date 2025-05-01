import {Injectable} from '@angular/core';
import {PutObjectCommand, S3Client} from '@aws-sdk/client-s3'

@Injectable({
  providedIn: 'root',
})
export class ProfilePictureService {
  private s3Client: S3Client;

  constructor() {
    this.s3Client = new S3Client({
      region: 'us-east-1',
      endpoint: 'http://localhost:4566',
      forcePathStyle: true,
      credentials: {
        accessKeyId: 'test',
        secretAccessKey: 'test'
      }
    });
  }

  async uploadProfilePicture(file: File, userEmail: string): Promise<string> {
    const fileName = `profile-pictures/${userEmail}-${Date.now()}-${file.name}`;

    const params = {
      Bucket: 'cdkstack-profile-pictures',
      Key: fileName,
      Body: file,
      ContentType: file.type,
    };

    try {
      const command = new PutObjectCommand(params);
      const res = await this.s3Client.send(command);
      console.log(res);

      return `http://localhost:4566/${params.Bucket}/${fileName}`;
    } catch (error) {
      console.error('Profile picture upload failed:', error);
      throw error;
    }
  }
}
