// Webhook ל-WhatsApp Cloud API (Meta).
// GET  — אימות ה-webhook מול Meta (hub.mode / hub.verify_token / hub.challenge).
// POST — קבלת הודעות נכנסות וסטטוסים. כרגע רק רושם ללוג של Vercel ומחזיר 200.
//
// משתני סביבה (מוגדרים ב-Vercel, לא בקוד):
//   VERIFY_TOKEN — מחרוזת שרירותית שמזינים גם במסך ה-Webhook של Meta.

module.exports = async (req, res) => {
  if (req.method === 'GET') {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];
    const expected = process.env.VERIFY_TOKEN;

    if (mode === 'subscribe' && expected && token === expected) {
      res.status(200).send(challenge);
      return;
    }
    res.status(403).send('Forbidden');
    return;
  }

  if (req.method === 'POST') {
    const body = req.body || {};
    try {
      const entries = Array.isArray(body.entry) ? body.entry : [];
      for (const entry of entries) {
        for (const change of entry.changes || []) {
          const value = change.value || {};
          const contacts = value.contacts || [];
          for (const msg of value.messages || []) {
            const contact = contacts.find((c) => c.wa_id === msg.from) || {};
            console.log(JSON.stringify({
              kind: 'message',
              id: msg.id,
              from: msg.from,
              name: contact.profile && contact.profile.name,
              type: msg.type,
              text: msg.text && msg.text.body,
              timestamp: msg.timestamp,
            }));
          }
          for (const st of value.statuses || []) {
            console.log(JSON.stringify({
              kind: 'status',
              id: st.id,
              status: st.status,
              recipient: st.recipient_id,
              timestamp: st.timestamp,
            }));
          }
        }
      }
    } catch (err) {
      console.error('webhook parse error', err && err.message);
    }
    // Meta מצפה ל-200 מהר, אחרת היא שולחת שוב.
    res.status(200).send('OK');
    return;
  }

  res.setHeader('Allow', 'GET, POST');
  res.status(405).end();
};
