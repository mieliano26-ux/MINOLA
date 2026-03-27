from flask import Flask, request
import os

app = Flask(__name__)

# זה ה-Webhook - ה"דלת" שדרכה מטא נכנסת
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # שלב האימות מול מטא
        verify_token = os.environ.get('VERIFY_TOKEN')
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == verify_token:
            return challenge, 200
        return 'Forbidden', 403

    if request.method == 'POST':
        # כאן הבוט יקבל את ההודעות מהלקוחות בעתיד
        data = request.get_json()
        print(f"Received message: {data}")
        return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
