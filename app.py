from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration - set these as environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

def send_email(name, sender_email, message, target_email):
    """
    Send email using the provided credentials
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = name  # Subject is the sender's name
        
        # Email body content
        body = f"""
Contact Form Submission

From: {name}
Email: {sender_email}
Message:
{message}

---
Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, target_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully from {name} ({sender_email}) to {target_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
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
        if not all([SENDER_EMAIL, SENDER_PASSWORD]):
            logger.error("Email configuration not properly set")
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
        if send_email(name, email, message, target_email):
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
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def index():
    """
    Basic info endpoint
    """
    return jsonify({
        'service': 'Email Middleware',
        'version': '1.0',
        'endpoints': {
            'POST /send-email': 'Send email from contact form',
            'GET /health': 'Health check'
        }
    }), 200

if __name__ == '__main__':
    # Check if required environment variables are set
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("ERROR: Please set the following environment variables:")
        print("- SENDER_EMAIL: The email address to send from")
        print("- SENDER_PASSWORD: The password for the sender email")
        print("\nOptional environment variables:")
        print("- SMTP_SERVER: SMTP server (default: smtp.gmail.com)")
        print("- SMTP_PORT: SMTP port (default: 587)")
        exit(1)
    
    print(f"Starting email middleware...")
    print(f"Sender: {SENDER_EMAIL}")
    print(f"SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    
    # Get port from environment variable (Render provides this)
    port = int(os.getenv('PORT', 5000))
    
    # Run the app
    app.run(debug=False, host='0.0.0.0', port=port)