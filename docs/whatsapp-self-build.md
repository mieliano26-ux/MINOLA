# וואטסאפ עצמאי — תוכנית וסטטוס

המטרה: לחבר את המספר של מיכלי (972502733773) ל‑WhatsApp Cloud API דרך אפליקציית Meta משלה,
כדי שאסטרו יקרא הודעות נכנסות בלי LetsBot. המספר ממשיך לעבוד גם באפליקציית WhatsApp Business בטלפון (coexistence).

קובץ זה הוא הזיכרון של הפרויקט. לעדכן אחרי כל שלב. לא לשמור כאן טוקנים, סיסמאות או App Secret.

## סטטוס (עודכן 2026-10-18)

| שלב | מה | סטטוס |
|---|---|---|
| 0 | החלטת ביניים לתקופה שבין סוף הניסיון ב‑LetsBot (20.10.2026) לסיום הבנייה | הוחלט: לא מחדשים את LetsBot, עובדים ידנית מהטלפון עד סיום הבנייה |
| 1 | אפליקציית Meta + Business Portfolio | לא התחיל |
| 2 | אימות עסק | לא התחיל |
| 3 | דף מדיניות פרטיות באתר MINOLA | בוצע. אומת בפריסת ניסיון מהטלפון של מיכלי (2026-10-18). באוויר ב‑production עם מיזוג PR #18 |
| 4 | שרת webhook + אחסון ב‑Vercel, בדיקה עם מספר הבדיקה | webhook באוויר עם מיזוג PR #18, `VERIFY_TOKEN` מוגדר ב‑Vercel. נשאר: בדיקה מול מספר הבדיקה של Meta, תלוי בשלב 1 |
| 5 | App Review (2 סרטונים + הרשאות) | לא התחיל |
| 6 | Embedded Signup + חיבור המספר ב‑coexistence | לא התחיל |
| 7 | חיבור לאסטרו + עדכון המשימה המתוזמנת "ווצאפ" | לא התחיל |

## מה ידוע [ודאי]

- LetsBot: ניסיון עד 20.10.2026 08:02. אין תוכנית בתשלום. המספר מחובר שם כ‑"official" (Cloud API).
- שימוש ב‑LetsBot ב‑30 הימים האחרונים: 24 הודעות נשלחו, 0 תשובות AI, 905 אנשי קשר.
- האתר מאוחסן ב‑Vercel, פרויקט `minola`, דומיין ייצור `minola-alpha.vercel.app`. אין דומיין מותאם.
- Vercel מחובר ל‑GitHub (mieliano26-ux), אפשר לפרוס מהריפו.
- הבוט הישן ב‑`main.py` (משחק תעלומה) לא פרוס בשום מקום ולא קשור לפרויקט הזה.

## החלטות

- 2026-10-18: התחלה מחדש. הקוד של שלבים 3 ו‑4 נכתב ונפרס בסשן אחד כדי לא לחכות ל‑Meta. PR #18 בריפו MINOLA.
- 2026-10-18: ניסיון לפרוס את הענף דרך ה‑API של Vercel (gitSource) על פרויקט `minola` שלא מקושר ל‑GitHub יצר פריסה ריקה: כל קובץ, כולל index.html, החזיר 404. בוצע rollback לפריסה הקודמת (dpl_EQdnmdfFECYp8SAV7r9njBRbky1n). לא לחזור על זה.
- 2026-10-18: מיכלי קישרה את פרויקט `minola` לריפו GitHub `mieliano26-ux/MINOLA` (Settings → Git). מעכשיו כל push ל‑main נפרס לבד, ו‑Vercel מעיר על PRים.
- 2026-10-18: גם אחרי הקישור הפריסה יצאה ריקה. [ודאי, אומת מול תיעוד Vercel ובפריסת ניסיון] הסיבה: `main.py` + `requirements.txt` בשורש גורמים ל‑Vercel לזהות את הריפו כאפליקציית Flask ולהתעלם מקובצי ה‑HTML. התיקון: `vercel.json` שמקבע framework=null ו‑`.vercelignore` שמוציא את קובצי ה‑Python מהפריסה.
- שלב 0 (הוחלט 2026-10-18, מיכלי: "אין לי כסף לזה"): לא לשלם ל‑LetsBot ולעבוד ידנית מהטלפון עד שהבנייה מסתיימת. הנימוק: 24 הודעות בחודש לא מצדיקות מנוי, והמספר ממשיך לעבוד בטלפון בכל מקרה.

## מזהים (לא סודיים)

- Vercel project: `prj_Jv3o9xRs2bFIAgvmzhKdmrTv6Wjr` (team `team_eHZVspG1Iw5wdAXT6fqg5jhY`)
- Meta App ID: —
- WABA ID: —
- Phone Number ID: —

## כתובות שיידרשו במסכים של Meta

- מדיניות פרטיות: `https://minola-alpha.vercel.app/privacy.html`
- מחיקת מידע (Data Deletion Instructions): `https://minola-alpha.vercel.app/privacy.html#deletion`
- Webhook Callback URL: `https://minola-alpha.vercel.app/api/webhook`
- Verify Token: שמור ב‑Vercel במשתנה `VERIFY_TOKEN` (Settings → Environment Variables). לא כאן.

## פתוח / לבדוק

- [לא מאומת] המסכים העדכניים ב‑Meta for Developers. התיעוד חסום מסביבת הענן, לאמת מול המסך בפועל.
- [ודאי] `minola-alpha.vercel.app` נגיש ציבורית: מיכלי קיבלה 404 של Vercel ולא מסך התחברות (2026-10-18).
- אימות חתימה (X-Hub-Signature-256 עם App Secret) ב‑webhook — להוסיף בשלב 7 לפני חיבור המספר האמיתי.
- איפה לשמור את ההודעות כדי שאסטרו יקרא אותן (שלב 7). כרגע רק לוג של Vercel.
