import re
LANGS = {"en": "English", "hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}

# Short templates (no festival / product-description logic needed here)
T = {
 "whatsapp_promo": {"en": "🙏 Hello! {shop} has {product} at ₹{price}/{unit}. Open {hours}. Message us to order!",
  "hi": "🙏 नमस्ते! {shop} में {product} सिर्फ़ ₹{price}/{unit}। समय: {hours}। ऑर्डर के लिए मैसेज करें!",
  "mr": "🙏 नमस्कार! {shop} येथे {product} फक्त ₹{price}/{unit}. वेळ: {hours}. ऑर्डरसाठी मेसेज करा!"},
 "social_caption": {"en": "{product} at {shop} ✨ ₹{price}/{unit} #LocalVendor #{tag}",
  "hi": "{shop} में {product} ✨ ₹{price}/{unit} #LocalVendor #{tag}", "mr": "{shop} येथे {product} ✨ ₹{price}/{unit} #LocalVendor #{tag}"},
 "marketing_tips": {
  "en": "1. Add your shop to Google Business Profile with photo, hours and area.\n2. Make a WhatsApp Business catalogue of your products.\n3. Keep a UPI QR from your bank or UPI app at the counter.\n4. Politely ask happy customers for a Google review.",
  "hi": "1. अपनी दुकान Google Business Profile पर फोटो, समय और इलाके के साथ जोड़ें।\n2. WhatsApp Business में अपने सामान का कैटलॉग बनाएँ।\n3. बैंक या UPI ऐप का QR काउंटर पर रखें।\n4. खुश ग्राहकों से विनम्रता से Google रिव्यू माँगें।",
  "mr": "1. तुमचे दुकान फोटो, वेळ आणि परिसरासह Google Business Profile वर जोडा.\n2. WhatsApp Business मध्ये मालाचा कॅटलॉग बनवा.\n3. बँक किंवा UPI अॅपचा QR काउंटरवर ठेवा.\n4. समाधानी ग्राहकांना नम्रपणे Google रिव्ह्यू मागा."}}

# Festival greetings: (emoji, {lang: greeting}). Keys are lowercase names/aliases the vendor might type.
_FEST = [
 (("diwali", "deepavali", "dipawali", "दिवाली", "दीपावली", "दिवाळी"), "🪔",
  {"en": "Happy Diwali", "hi": "दीपावली की हार्दिक शुभकामनाएँ", "mr": "दिवाळीच्या हार्दिक शुभेच्छा"}),
 (("holi", "होली", "होळी"), "🎨",
  {"en": "Happy Holi", "hi": "होली की हार्दिक शुभकामनाएँ", "mr": "होळीच्या हार्दिक शुभेच्छा"}),
 (("eid", "eid mubarak", "eid al-fitr", "eid ul fitr", "eid al-adha", "bakrid", "ईद", "ईद मुबारक"), "🌙",
  {"en": "Eid Mubarak", "hi": "ईद मुबारक", "mr": "ईद मुबारक"}),
 (("ganesh chaturthi", "ganpati", "ganesh utsav", "गणेश चतुर्थी", "गणपती", "गणेशोत्सव"), "🙏",
  {"en": "Happy Ganesh Chaturthi", "hi": "गणेश चतुर्थी की हार्दिक शुभकामनाएँ", "mr": "गणपती बाप्पा मोरया! गणेश चतुर्थीच्या हार्दिक शुभेच्छा"}),
 (("navratri", "navaratri", "नवरात्रि", "नवरात्री", "नवरात्र"), "💃",
  {"en": "Happy Navratri", "hi": "नवरात्रि की हार्दिक शुभकामनाएँ", "mr": "नवरात्रीच्या हार्दिक शुभेच्छा"}),
 (("dussehra", "dasara", "vijayadashami", "दशहरा", "दसरा"), "🏹",
  {"en": "Happy Dussehra", "hi": "दशहरा की हार्दिक शुभकामनाएँ", "mr": "दसऱ्याच्या हार्दिक शुभेच्छा"}),
 (("raksha bandhan", "rakhi", "rakshabandhan", "रक्षाबंधन", "राखी"), "🧵",
  {"en": "Happy Raksha Bandhan", "hi": "रक्षाबंधन की हार्दिक शुभकामनाएँ", "mr": "रक्षाबंधनाच्या हार्दिक शुभेच्छा"}),
 (("christmas", "xmas", "क्रिसमस", "नाताळ"), "🎄",
  {"en": "Merry Christmas", "hi": "क्रिसमस की हार्दिक शुभकामनाएँ", "mr": "नाताळच्या हार्दिक शुभेच्छा"}),
 (("makar sankranti", "sankranti", "uttarayan", "मकर संक्रांति", "मकर संक्रांत", "संक्रांति", "संक्रांत"), "🪁",
  {"en": "Happy Makar Sankranti", "hi": "मकर संक्रांति की हार्दिक शुभकामनाएँ", "mr": "तिळगूळ घ्या, गोड गोड बोला! मकर संक्रांतीच्या हार्दिक शुभेच्छा"}),
 (("gudi padwa", "ugadi", "गुड़ी पड़वा", "गुढीपाडवा", "गुढी पाडवा"), "🚩",
  {"en": "Happy Gudi Padwa", "hi": "गुड़ी पड़वा की हार्दिक शुभकामनाएँ", "mr": "गुढीपाडव्याच्या हार्दिक शुभेच्छा"}),
 (("independence day", "स्वतंत्रता दिवस", "स्वातंत्र्य दिन"), "🇮🇳",
  {"en": "Happy Independence Day", "hi": "स्वतंत्रता दिवस की हार्दिक शुभकामनाएँ", "mr": "स्वातंत्र्य दिनाच्या हार्दिक शुभेच्छा"}),
 (("republic day", "गणतंत्र दिवस", "प्रजासत्ताक दिन"), "🇮🇳",
  {"en": "Happy Republic Day", "hi": "गणतंत्र दिवस की हार्दिक शुभकामनाएँ", "mr": "प्रजासत्ताक दिनाच्या हार्दिक शुभेच्छा"}),
]


def festival_wish(name, lang):
    """Return (emoji, greeting) for a festival name; generic greeting for names we do not know."""
    n = (name or "").strip().lower()
    for keys, emoji, wish in _FEST:
        if n in keys or any(k in n for k in keys if len(k) > 3):
            return emoji, wish[lang]
    name = (name or "").strip() or "Festival"
    return "🎉", {"en": f"Happy {name}", "hi": f"{name} की हार्दिक शुभकामनाएँ", "mr": f"{name} निमित्त हार्दिक शुभेच्छा"}[lang]


FEST_T = {
 "en": "{emoji} {wish} from {shop}!\nCelebrate with our {product} at ₹{price}/{unit}. We are open {hours}{area}. Visit us with your family and friends!",
 "hi": "{emoji} {shop} की ओर से {wish}!\nइस त्योहार पर हमारा {product} ₹{price}/{unit} में आज़माएँ। समय: {hours}{area}। परिवार और दोस्तों के साथ ज़रूर आइए!",
 "mr": "{emoji} {shop} तर्फे {wish}!\nया सणानिमित्त आमचे {product} ₹{price}/{unit} मध्ये अवश्य चाखा. वेळ: {hours}{area}. कुटुंब आणि मित्रांसह नक्की या!",
}
DESC_T = {
 "en": "{product} at {shop}, your local {biz}. {desc}Available for ₹{price} per {unit}. We are open {hours}{area}.",
 "hi": "{shop} ({biz}) का {product}। {desc}कीमत ₹{price} प्रति {unit}। हम {hours} खुले रहते हैं{area}।",
 "mr": "{shop} ({biz}) चे {product}. {desc}किंमत ₹{price} प्रति {unit}. आम्ही {hours} खुले असतो{area}.",
}
AREA = {"en": ", serving {a}", "hi": " ({a} में)", "mr": " ({a} परिसरात)"}
PRODUCT_TASKS = {"product_description", "whatsapp_promo", "festival_offer", "social_caption"}


def _sentence(d):
    d = (d or "").strip()
    if not d: return ""
    return d + ("" if d[-1] in ".!?।" else ".") + " "


def demo_text(task, lang, v, p, festival):
    p = p or {}
    area = (v.get("service_area") or "").strip()
    f = dict(shop=v["shop_name"], product=p.get("name", ""), price=f"{p.get('price', 0):g}", unit=p.get("unit", ""),
             hours=v["opening_hours"], biz=v["business_type"], area=AREA[lang].format(a=area) if area else "")
    if task == "festival_offer":
        f["emoji"], f["wish"] = festival_wish(festival, lang)
        return FEST_T[lang].format(**f).strip()
    if task == "product_description":
        return DESC_T[lang].format(desc=_sentence(p.get("description")), **f).strip()
    return T[task][lang].format(desc=p.get("description") or "", festival=festival or "Festival", hours=f["hours"],
        shop=f["shop"], product=f["product"], price=f["price"], unit=f["unit"], tag=re.sub(r"\W", "", v["shop_name"])).strip()


def build_prompt(task, lang, v, p, festival):
    sysmsg = ("You help Indian street vendors write short, honest marketing text. Use simple words. "
              f"Write ONLY in {LANGS[lang]}. Use only the facts given. Do not invent discounts, offers, prices, ingredients, health claims, "
              "awards or guarantees. Never ask for UPI PIN, OTP or passwords. Output just the text, no heading and no explanation.")
    facts = f"Shop: {v['shop_name']} ({v['business_type']}). Hours: {v['opening_hours']}. Area: {v.get('service_area') or 'n/a'}."
    if p: facts += f" Product: {p['name']}, ₹{p['price']:g} per {p['unit']}. Note: {p.get('description') or 'none'}."
    fest = festival or "the festival"
    ask = {"product_description": "Write a 2 to 3 sentence description of this product for customers. Mention the product name, the price per unit and the shop opening hours, using only the facts above.",
           "whatsapp_promo": "Write a friendly WhatsApp promo under 60 words.",
           "festival_offer": (f"Write a short, warm {fest} greeting from the shop (start with the festival wish in {LANGS[lang]}), "
                              f"then invite customers to try this product. Mention the price and opening hours. Do not invent any discount or offer. Under 60 words."),
           "social_caption": "Write an Instagram/Facebook caption with 3 hashtags.",
           "marketing_tips": "Give 4 practical digital marketing, customer engagement and local SEO tips as a numbered list."}[task]
    return sysmsg, f"{facts}\n{ask}"

BAD = [r"\bguarantee[sd]?\b", r"100\s*%\s*(profit|safe|cure)", r"\b(cures?|miracle)\b", r"\b(share|send|enter)\b.{0,20}\b(otp|pin|password)\b"]
def validate(text):
    t = (text or "").strip()
    if len(t) < 10: return False, "Draft was too short."
    if len(t) > 2000: return False, "Draft was too long."
    if "<" in t or ">" in t: return False, "Draft contained markup."
    for b in BAD:
        if re.search(b, t, re.I): return False, "Draft contained a risky claim."
    return True, ""

SCHEMES = [
 {"name": "PM SVANidhi", "for": "Street vendors", "summary": "Central government micro-credit scheme for street vendors.", "link": "https://pmsvanidhi.mohua.gov.in/"},
 {"name": "Udyam Registration", "for": "Small businesses", "summary": "Free online MSME registration on the government portal.", "link": "https://udyamregistration.gov.in/"},
 {"name": "FSSAI licence/registration", "for": "Food vendors", "summary": "Food safety registration via FoSCoS.", "link": "https://foscos.fssai.gov.in/"}]
SCHEME_NOTE = ("Only names and official links are listed. Amounts, eligibility and documents change, so DukaanSaathi does not copy them. "
               "Check the official site or your local municipal office. This is information, not an application.")
UPI = ["Use your existing bank account, or visit your bank if you need help opening one.",
 "Install an official UPI app (BHIM, or your bank's app) from Google Play or the App Store.",
 "Link your mobile number and bank account inside the app. The app asks for your UPI PIN only on its own screen.",
 "Open 'QR code' or 'Receive money' in the app to see your personal QR. Many banks also issue a merchant QR on request.",
 "Print the QR and place it at the counter. Test with a ₹1 payment from a friend."]
UPI_SAFETY = "Never tell anyone your UPI PIN, OTP or bank password. To RECEIVE money you never enter a PIN. DukaanSaathi cannot create accounts or move money."