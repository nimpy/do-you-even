import streamlit as st
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
REDIRECT_URI = 'http://localhost:8501/'
DOCUMENT_ID = os.getenv('GOOGLE_DOC_ID')

def check_configuration():
    """Check if all required configuration is present"""
    if not DOCUMENT_ID:
        st.error("""
        Missing GOOGLE_DOC_ID in environment variables. 
        Please create a .env file with your Google Doc ID:
        
        GOOGLE_DOC_ID=your_document_id_here
        """)
        return False
    if not os.path.exists('client_secrets.json'):
        st.error("""
        Missing client_secrets.json file. 
        Please download it from Google Cloud Console and place it in this directory.
        """)
        return False
    return True

def create_flow():
    return Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

def load_or_create_credentials():
    creds = None
    
    if 'google_creds' in st.session_state:
        creds = Credentials(**st.session_state.google_creds)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = create_flow()
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            st.markdown(f'### Google Login')
            st.markdown(f'Click the button below to log in with Google:')
            st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#4285F4;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">Login with Google</button></a>', unsafe_allow_html=True)
            
            try:
                code = st.query_params.get('code', [None])[0]
                if code:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    
                    st.session_state.google_creds = {
                        'token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_uri': creds.token_uri,
                        'client_id': creds.client_id,
                        'client_secret': creds.client_secret,
                        'scopes': creds.scopes
                    }
                    st.experimental_rerun()
            except Exception as e:
                st.error(f'Error during authentication: {str(e)}')
                return None
    
    return creds

def read_workout_doc(creds):
    """Read content from specific Google Doc"""
    try:
        docs_service = build('docs', 'v1', credentials=creds)
        document = docs_service.documents().get(documentId=DOCUMENT_ID).execute()
        
        content = []
        for elem in document.get('body').get('content'):
            if 'paragraph' in elem:
                for para_elem in elem.get('paragraph').get('elements'):
                    if 'textRun' in para_elem:
                        content.append(para_elem.get('textRun').get('content'))
        
        return ''.join(content)
    except Exception as e:
        st.error(f'Error reading document: {str(e)}')
        return None

def main():
    st.title('Workout Tracker')
    
    # Check configuration before proceeding
    if not check_configuration():
        return
        
    # Authenticate with Google
    creds = load_or_create_credentials()
    
    if not creds:
        return
    
    if creds:
        st.success('Successfully authenticated with Google!')
        
        try:
            content = read_workout_doc(creds)
            if content:
                st.subheader('Recent workouts:')
                st.text(content)
            else:
                st.warning('Could not read the workout document. Please check the document ID.')
                
        except Exception as e:
            st.error(f'Error accessing Google Doc: {str(e)}')

if __name__ == '__main__':
    main()