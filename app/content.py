import re
LANGS = {"en": "English", "hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}
T = {
 "whatsapp_promo": {"en": "🙏 Hello! {shop} has {product} at ₹{price}/{unit}. Open {hours}. Message us to order!",
  "hi": "🙏 नमस्ते! {shop} में {product} सिर्फ़ ₹{price}/{unit}। समय: {hours}। ऑर्डर के लिए मैसेज करें!",
  "mr": "🙏 नमस्कार! {shop} येथे {product} फक्त ₹{price}/{unit}. वेळ: {hours}. ऑर्डरसाठी मेसेज करा!"},
 "product_description": {"en": "{product} from {shop}, priced at ₹{price} per {unit}. {desc}",
  "hi": "{shop} का {product}, ₹{price} प्रति {unit}। {desc}", "mr": "{shop} चे {product}, ₹{price} प्रति {unit}. {desc}"},
 "festival_offer": {"en": "🎉 {festival} special at {shop}! Try our {product} at ₹{price}/{unit}. Tell your family and friends!",
  "hi": "🎉 {festival} स्पेशल – {shop}! हमारा {product} ₹{price}/{unit} में। परिवार और दोस्तों को बताएँ!",
  "mr": "🎉 {festival} स्पेशल – {shop}! आमचे {product} ₹{price}/{unit} मध्ये. कुटुंब आणि मित्रांना सांगा!"},
 "social_caption": {"en": "{product} at {shop} ✨ ₹{price}/{unit} #LocalVendor #{tag}",
  "hi": "{shop} में {product} ✨ ₹{price}/{unit} #LocalVendor #{tag}", "mr": "{shop} येथे {product} ✨ ₹{price}/{unit} #LocalVendor #{tag}"},
 "marketing_tips": {
  "en": "1. Add your shop to Google Business Profile with photo, hours and area.\n2. Make a WhatsApp Business catalogue of your products.\n3. Keep a UPI QR from your bank or UPI app at the counter.\n4. Politely ask happy customers for a Google review.",
  "hi": "1. अपनी दुकान Google Business Profile पर फोटो, समय और इलाके के साथ जोड़ें।\n2. WhatsApp Business में अपने सामान का कैटलॉग बनाएँ।\n3. बैंक या UPI ऐप का QR काउंटर पर रखें।\n4. खुश ग्राहकों से विनम्रता से Google रिव्यू माँगें।",
  "mr": "1. तुमचे दुकान फोटो, वेळ आणि परिसरासह Google Business Profile वर जोडा.\n2. WhatsApp Business मध्ये मालाचा कॅटलॉग बनवा.\n3. बँक किंवा UPI अॅपचा QR काउंटरवर ठेवा.\n4. समाधानी ग्राहकांना नम्रपणे Google रिव्ह्यू मागा."}}
PRODUCT_TASKS = {"product_description", "whatsapp_promo", "festival_offer", "social_caption"}

def demo_text(task, lang, v, p, festival):
    p = p or {}
    return T[task][lang].format(shop=v["shop_name"], product=p.get("name", ""), price=f"{p.get('price', 0):g}",
        unit=p.get("unit", ""), hours=v["opening_hours"], desc=p.get("description") or "",
        festival=festival or "Festival", tag=re.sub(r"\W", "", v["shop_name"])).strip()

def build_prompt(task, lang, v, p, festival):
    sysmsg = ("You help Indian street vendors write short, honest marketing text. Use simple words. "
              f"Write ONLY in {LANGS[lang]}. Use only the facts given. Do not invent discounts, prices, health claims, "
              "awards or guarantees. Never ask for UPI PIN, OTP or passwords. Output just the text.")
    facts = f"Shop: {v['shop_name']} ({v['business_type']}). Hours: {v['opening_hours']}. Area: {v.get('service_area') or 'n/a'}."
    if p: facts += f" Product: {p['name']}, ₹{p['price']:g} per {p['unit']}. Note: {p.get('description') or 'none'}."
    ask = {"product_description": "Write a 2-sentence product description.", "whatsapp_promo": "Write a friendly WhatsApp promo under 60 words.",
           "festival_offer": f"Write a festival message for {festival or 'the festival'} without inventing any discount.",
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
