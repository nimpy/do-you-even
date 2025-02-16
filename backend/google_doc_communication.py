from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleDocsClient:
    def __init__(self):
        self.document_id = os.getenv('GOOGLE_DOC_ID')
        self.credentials = self._get_credentials()
        self.service = build('docs', 'v1', credentials=self.credentials)

    def _get_credentials(self) -> service_account.Credentials:
        """Get credentials from service account json file"""
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path or not os.path.exists(credentials_path):
            raise ValueError("Missing or invalid GOOGLE_APPLICATION_CREDENTIALS environment variable")
            
        return service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )

    def read_document(self) -> Optional[str]:
        """Read content from the workout document"""
        try:
            document = self.service.documents().get(documentId=self.document_id).execute()
            
            content = []
            for elem in document.get('body', {}).get('content', []):
                if 'paragraph' in elem:
                    for para_elem in elem['paragraph'].get('elements', []):
                        if 'textRun' in para_elem:
                            content.append(para_elem['textRun'].get('content', ''))
            
            return ''.join(content)
            
        except Exception as e:
            print(f"Error reading document: {str(e)}")
            return None