from flask import Flask, request
import os
import requests
import random

app = Flask(__name__)

# --- מאגרי הנתונים של מינולה (ה"מוח") ---

CHEEKY_REPLIES = [
    "מה נראה לכם, שאני עובדת אצלכם? אה רגע, בעצם כן. מה הלוז? 🙄",
    "מיכלי, הקבוצה הזאת חופרת. אפשר לחלק להם משימות חובה? 💅",
    "קראתי את מה שכתבתם. בחרתי להתעלם. אבל הנה אני פה. דברו.",
    "מישהו אמר 'צ'יטה' ולא קיבל? אני פה, תרגיעו.",
    "אני בסטרס נומרולוגי, אז כדאי שההודעה הבאה תהיה מעניינת. 🔮"
]

GAMES = {
    "מי הכי": [
        "מי הכי סביר שיישאר עם שקל בבנק אבל יקנה נעליים ב-2000? 💸",
        "מי הכי סביר שייעלם מהקבוצה לשבוע ואז יחזור כאילו כלום? 👻",
        "מי הכי סביר שישלח הודעה קולית של 4 דקות? 🎤"
    ],
    "משימה": [
        "כולם לשלוח עכשיו סלפי עם הפרצוף הכי מצחיק שלכם! מי שלא שולח - מקבל קנס צ'יטות! 📸",
        "תייגו את הבנאדם הכי חופר בקבוצה עכשיו. בלי רחמים. 😈",
        "יש לכם דקה לשלוח תמונה של מה שאתם אוכלים עכשיו. צאו!"
    ]
}

# --- לוגיקה של הבוט ---

def get_bot_response(user_text):
    user_text = user_text.lower()
    
    if "מי הכי" in user_text:
        return f"שאלה מעולה! {random.choice(GAMES['מי הכי'])}"
    
    if "משימה" in user_text or "משחק" in user_text:
        return f"יאללה אקשן: {random.choice(GAMES['משימה'])}"
    
    if "צ'יטה" in user_text or "כסף" in user_text:
        return "צ'יטות? כרגע יש לכם אפס. תתחילו לעבוד בשבילן! 🐆"
    
    # ברירת מחדל - תגובה חצופה
    return random.choice(CHEEKY_REPLIES)

# --- ניהול הוובהוק (Webhook) ---

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = os.environ.get('VERIFY_TOKEN')
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == verify_token:
            return challenge, 200
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.get_json()
        try:
            if 'messages' in data['entry'][0]['changes'][0]['value']:
                message_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
                from_number = message_obj['from']
                user_text = message_obj.get('text', {}).get('body', '')

                # שליפת תגובה מה"מוח"
                bot_reply = get_bot_response(user_text)
                
                send_whatsapp_message(from_number, bot_reply)
        except Exception as e:
            print(f"Error: {e}")
            
        return 'OK', 200

def send_whatsapp_message(to, text):
    access_token = os.environ.get('ACCESS_TOKEN')
    phone_number_id = os.environ.get('PHONE_NUMBER_ID')
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
