from flask import Flask, request
import os
import requests
import random

app = Flask(__name__)

# --- בסיס נתונים זמני בזיכרון ---
reveal_state = {
    "active": False,
    "guesses": 0,
    "target_guesses": 3,
    "answer": "נועם",  # דוגמה לתשובה
    "mystery": "מישהו בקבוצה הזאת לא מפסיק לחפור היום. מי זה?"
}

def get_reveal_logic(user_text):
    global reveal_state
    user_text = user_text.lower()

    # שלב 1: התחלת תעלומה (Trigger)
    if "תעלומה" in user_text or "משחק" in user_text:
        reveal_state["active"] = True
        reveal_state["guesses"] = 0
        return f"🔥 {reveal_state['mystery']} \n(צריך 3 ניחושים כדי שאגלה!)"

    # שלב 2+3: ספירת אינטראקציה ומתן רמזים
    if reveal_state["active"]:
        reveal_state["guesses"] += 1
        
        if reveal_state["guesses"] == 1:
            return "❌ לא נכון! רמז ראשון: זה מישהו שיש לו הומור שנון מדי."
        
        if reveal_state["guesses"] == 2:
            return "❌ קרוב, אבל לא! רמז אחרון: השם שלו מתחיל ב-נ'."
        
        # שלב 4: החשיפה הסופית
        if reveal_state["guesses"] >= reveal_state["target_guesses"]:
            reveal_state["active"] = False
            return f"🎉 הגיע הזמן לגלות! זה {reveal_state['answer']}! תפסיק לחפור וקבל צ'יטה! 🐆"

    return "אני שומעת אתכם... דברו אליי ב'תעלומה' אם אתם רוצים אקשן. 💅"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('VERIFY_TOKEN'):
            return request.args.get('hub.challenge'), 200
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.get_json()
        try:
            message_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message_obj['from']
            user_text = message_obj.get('text', {}).get('body', '')
            
            # הפעלת מנגנון החשיפה
            response = get_reveal_logic(user_text)
            send_whatsapp_message(from_number, response)
        except: pass
        return 'OK', 200

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v17.0/{os.environ.get('PHONE_NUMBER_ID')}/messages"
    headers = {"Authorization": f"Bearer {os.environ.get('ACCESS_TOKEN')}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
