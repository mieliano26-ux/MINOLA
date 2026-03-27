from flask import Flask, request
import os
import requests

app = Flask(__name__)

# הגדרות מה-Environment של Render
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # אימות מול מטא
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return 'Error, wrong validation token', 403

    if request.method == 'POST':
        data = request.get_json()
        
        # בדיקה שיש הודעה בתוך המידע שהגיע
        try:
            if data.get('entry') and data['entry'][0].get('changes') and data['entry'][0]['changes'][0]['value'].get('messages'):
                message = data['entry'][0]['changes'][0]['value']['messages'][0]
                from_number = message['from']  # המספר של השולח
                
                # שליחת הודעת תשובה אוטומטית
                send_whatsapp_message(from_number, "היי! כאן מינולה. הבוט שלך רשמית בחיים! 🚀")
        except Exception as e:
            print(f"Error processing message: {e}")

        return 'OK', 200

def send_whatsapp_message(to_number, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Message sent! Response: {response.status_code}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
