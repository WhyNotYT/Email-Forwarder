from flask import Flask, request, jsonify
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import requests

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resend configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_NAME = os.getenv('SENDER_NAME', 'Contact Form')

def send_email_resend(name, sender_email, message, target_email):
    """
    Send email using Resend API
    """
    try:
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
            "to": [target_email],
            "subject": name,  # Subject is the sender's name
            "text": f"""
Contact Form Submission

From: {name}
Email: {sender_email}
Message:
{message}

---
Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully from {name} ({sender_email}) to {target_email}")
            return True
        else:
            logger.error(f"Resend error: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {str(e)}")
        return False

@app.route('/send-email', methods=['POST'])
def handle_email():
    """
    Handle incoming JSON requests and send emails
    """
    try:
        # Check if request contains JSON
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'message', 'target_email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Check if email configuration is set
        if not all([RESEND_API_KEY, SENDER_EMAIL]):
            logger.error("Resend configuration not properly set")
            return jsonify({
                'success': False,
                'error': 'Server email configuration error'
            }), 500
        
        # Extract data
        name = data['name'].strip()
        email = data['email'].strip()
        message = data['message'].strip()
        target_email = data['target_email'].strip()
        
        # Basic validation
        if not name or not email or not message or not target_email:
            return jsonify({
                'success': False,
                'error': 'All fields must contain valid content'
            }), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'Invalid sender email format'
            }), 400
            
        if '@' not in target_email or '.' not in target_email:
            return jsonify({
                'success': False,
                'error': 'Invalid target email format'
            }), 400
        
        # Send email
        if send_email_resend(name, email, message, target_email):
            return jsonify({
                'success': True,
                'message': 'Email sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send email'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'email_service': 'Resend'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """
    Basic info endpoint
    """
    return jsonify({
        'service': 'Email Middleware (Resend)',
        'version': '1.0',
        'endpoints': {
            'POST /send-email': 'Send email from contact form',
            'GET /health': 'Health check'
        }
    }), 200

if __name__ == '__main__':
    # Check if required environment variables are set
    if not RESEND_API_KEY or not SENDER_EMAIL:
        print("ERROR: Please set the following environment variables:")
        print("- RESEND_API_KEY: Your Resend API key")
        print("- SENDER_EMAIL: The verified sender email address")
        print("\nOptional environment variables:")
        print("- SENDER_NAME: The sender name (default: Contact Form)")
        exit(1)
    
    print(f"Starting email middleware with Resend...")
    print(f"Sender: {SENDER_EMAIL}")
    
    # Get port from environment variable (Render provides this)
    port = int(os.getenv('PORT', 5000))
    
    # Run the app
    app.run(debug=False, host='0.0.0.0', port=port)