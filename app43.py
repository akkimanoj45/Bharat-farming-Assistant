from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import requests
import os

app = Flask(__name__)

chat_memory = []

# ================== 🔑 PUT YOUR KEYS HERE ==================
GROQ_API_KEY = "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"
WEATHER_API_KEY = "2b46ee663df58c9c5289e6a614005e10"
MANDI_API_KEY= "579b464db66ec23bdd00000161d7e9b7b5dc4cb45006f93ed3bc01f2"

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Bharat Farming Assistant AI.
Give very short practical answers (maximum 3 lines).
Use simple farmer-friendly language.
Warn before spraying if rain or humidity is high.
Reply only in selected language.
"""

# ================== WEATHER ==================
@app.route("/get_weather")
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Bijapur&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["main"]
        city = data["name"]

        spray_alert = "Safe for spraying"
        irrigation_advice = "Normal irrigation"

        if "Rain" in condition or humidity > 80:
            spray_alert = "⚠ Avoid spraying today"

        if temp > 35:
            irrigation_advice = "Increase irrigation due to heat"

        if temp < 18:
            irrigation_advice = "Reduce irrigation, cool weather"

        return jsonify({
            "temp": temp,
            "humidity": humidity,
            "condition": condition,
            "spray": spray_alert,
            "irrigation": irrigation_advice,
            "city": city
        })
    except:
        return jsonify({"error": "Weather offline"})

@app.route("/irrigation_advice")
def irrigation_advice():
    try:
        crop = request.args.get("crop", "General")
        temp = float(request.args.get("temp", 30))
        humidity = float(request.args.get("humidity", 50))

        advice = "Normal irrigation"

        if temp > 35:
            advice = f"{crop}: Increase water supply due to high heat."
        elif temp < 18:
            advice = f"{crop}: Reduce irrigation. Cool weather."
        elif humidity > 80:
            advice = f"{crop}: Skip irrigation today. High moisture."
        else:
            advice = f"{crop}: Moderate irrigation every 2-3 days."

        return jsonify({"advice": advice})

    except:
        return jsonify({"error": "Irrigation error"})

# ================== FERTILIZER ENGINE ==================
# ================== ADVANCED FERTILIZER ENGINE WITH LANGUAGE ==================
@app.route("/fertilizer_advice")
def fertilizer_advice():
    crop = request.args.get("crop", "").lower()
    stage = request.args.get("stage", "").lower()
    language = request.args.get("lang", "English")

    fertilizer_data = {

         "rice": {
            "early": "Apply NPK 20:10:10 (Basal dose) + Zinc.",
            "mid": "Top dress Urea after 25 days.",
            "late": "Apply Potash for grain filling."
        },

        "wheat": {
            "early": "Apply DAP during sowing.",
            "mid": "Apply Urea after 30 days.",
            "late": "Apply light Nitrogen + Sulphur."
        },

        "maize": {
            "early": "Apply NPK 20:20:0 at sowing.",
            "mid": "Top dress Urea at knee stage.",
            "late": "Apply Potash before tasseling."
        },

        "cotton": {
            "early": "Apply NPK 20:20:0 basal dose.",
            "mid": "Apply Urea + Boron spray.",
            "late": "Apply Potash 0:0:50."
        },

        "sugarcane": {
            "early": "Apply NPK 10:26:26.",
            "mid": "Top dress Urea in 2 splits.",
            "late": "Apply Potash for sweetness."
        },

        "tomato": {
            "early": "Apply NPK 19:19:19.",
            "mid": "Apply NPK 12:61:00 during flowering.",
            "late": "Apply Potash rich fertilizer."
        },

        "potato": {
            "early": "Apply DAP + Potash.",
            "mid": "Apply Urea 25 days after planting.",
            "late": "Apply Potash for tuber growth."
        },

        "onion": {
            "early": "Apply NPK 20:10:10.",
            "mid": "Apply Urea + Sulphur.",
            "late": "Apply Potash spray."
        },

        "chilli": {
            "early": "Apply NPK 19:19:19.",
            "mid": "Apply NPK 00:52:34 for flowering.",
            "late": "Apply Potash spray."
        },

        "banana": {
            "early": "Apply NPK 15:15:15.",
            "mid": "Apply Urea + Micronutrients.",
            "late": "Apply Potash 0:0:50."
        },

        "groundnut": {
            "early": "Apply Gypsum + DAP.",
            "mid": "Apply Urea in small quantity.",
            "late": "Apply Calcium spray."
        },

        "soybean": {
            "early": "Apply DAP + Rhizobium culture.",
            "mid": "Apply NPK 19:19:19 spray.",
            "late": "Apply Potash."
        },

        "pigeonpea": {
            "early": "Apply DAP + Rhizobium culture.",
            "mid": "Apply NPK 19:19:19 spray.",
            "late": "Apply Sulphur spray."
        }

    }
    organic_tip = "Use vermicompost + neem cake as organic option."

    if crop in fertilizer_data and stage in fertilizer_data[crop]:
        recommendation = fertilizer_data[crop][stage]
    else:
        recommendation = "Use balanced NPK 20:20:20 fertilizer."

    # If language not English → translate using AI
    if language != "English":
        translate_prompt = f"""
        Translate the following fertilizer advice into {language}.
        Keep it short and farmer friendly.

        Advice:
        {recommendation}

        Organic Tip:
        {organic_tip}
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": translate_prompt}],
        )

        translated = completion.choices[0].message.content
        return jsonify({"recommendation": translated})

    return jsonify({
        "recommendation": recommendation,
        "organic": organic_tip
    })

@app.route("/chat", methods=["POST"])
def chat():
    global chat_memory

    data = request.json
    message = data.get("message")
    language = data.get("language", "English")

    try:
        chat_memory.append({"role": "user", "content": message})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Reply strictly in {language}."}
        ]

        # include last 6 messages for memory
        messages += chat_memory[-6:]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )

        reply = completion.choices[0].message.content

        chat_memory.append({"role": "assistant", "content": reply})

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "AI error: " + str(e)})

# ================== EXTENDED CROP CALENDAR ==================


# ================== MANDI API (UPDATED) ==================
# ================== MASTER DATA (All Crops, States, Districts) ==================
# ================== KARNATAKA MANDI ONLY ==================
# ================== KARNATAKA LOCAL FILTER VERSION ==================
@app.route("/get_mandi")
def get_mandi():
    try:
        crop = request.args.get("crop", "").lower()
        district = request.args.get("district", "").lower()

        base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

        params = {
            "api-key": MANDI_API_KEY,
            "format": "json",
            "limit": 1000
        }

        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()

        records = data.get("records", [])
        result = []

        for r in records:

            r_state = str(r.get("state", "")).lower()
            r_crop = str(r.get("commodity", "")).lower()
            r_district = str(r.get("district", "")).lower()

            # Force Karnataka filter locally
            if "karnataka" not in r_state:
                continue

            if crop and crop not in r_crop:
                continue

            if district and district not in r_district:
                continue

            result.append({
                "commodity": r.get("commodity"),
                "market": r.get("market"),
                "district": r.get("district"),
                "min_price": r.get("min_price"),
                "max_price": r.get("max_price"),
                "modal_price": r.get("modal_price")
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})
# ================== KARNATAKA DISTRICTS ==================
@app.route("/get_karnataka_districts")
def get_karnataka_districts():
    try:
        base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

        params = {
            "api-key": MANDI_API_KEY,
            "format": "json",
            "limit": 1000
        }

        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()

        records = data.get("records", [])
        districts = set()

        for r in records:
            if "karnataka" in str(r.get("state", "")).lower():
                districts.add(r.get("district"))

        return jsonify(sorted(list(districts)))

    except Exception as e:
        return jsonify({"error": str(e)})

# ================== GOVERNMENT SCHEMES (EXPANDED REAL DATA) ==================
@app.route("/get_schemes")
def get_schemes():

    category = request.args.get("category", "").lower()

    schemes = {

        "income": [
            {
                "name": "PM-KISAN",
                "description": "₹6000 yearly income support to farmer families.",
                "eligibility": "Small & marginal farmers.",
                "apply": "https://pmkisan.gov.in",
                "helpline": "155261 / 1800-115-526"
            },
            {
                "name": "Raitha Vidya Nidhi (Karnataka)",
                "description": "Scholarship for children of farmers.",
                "eligibility": "Farmers’ children studying in Karnataka.",
                "apply": "https://raitamitra.karnataka.gov.in",
                "helpline": "Karnataka Agriculture Dept."
            }
        ],

        "insurance": [
            {
                "name": "PM Fasal Bima Yojana (PMFBY)",
                "description": "Crop insurance against natural calamities.",
                "eligibility": "Farmers growing notified crops.",
                "apply": "https://pmfby.gov.in",
                "helpline": "14447"
            },
            {
                "name": "Livestock Insurance Scheme",
                "description": "Insurance for cattle & livestock.",
                "eligibility": "Dairy farmers.",
                "apply": "https://dahd.nic.in",
                "helpline": "Department of Animal Husbandry"
            }
        ],

        "loan": [
            {
                "name": "Kisan Credit Card (KCC)",
                "description": "Low interest crop loan.",
                "eligibility": "Farmers with land records.",
                "apply": "https://www.india.gov.in/spotlight/kisan-credit-card-kcc",
                "helpline": "Nearest nationalized bank"
            },
            {
                "name": "Agri Infrastructure Fund",
                "description": "Loan for agri storage & infrastructure.",
                "eligibility": "Farmers & FPOs.",
                "apply": "https://agriinfra.dac.gov.in",
                "helpline": "Ministry of Agriculture"
            }
        ],

        "subsidy": [
            {
                "name": "PM Kusum Solar Scheme",
                "description": "Subsidy for solar irrigation pumps.",
                "eligibility": "Farmers with irrigation land.",
                "apply": "https://pmkusum.mnre.gov.in",
                "helpline": "1800-180-3333"
            },
            {
                "name": "National Horticulture Mission",
                "description": "Subsidy for horticulture crops & nursery.",
                "eligibility": "Farmers growing fruits/vegetables.",
                "apply": "https://nhb.gov.in",
                "helpline": "Horticulture Dept."
            }
        ],

        "irrigation": [
            {
                "name": "PM Krishi Sinchai Yojana",
                "description": "Support for drip & sprinkler irrigation.",
                "eligibility": "Farmers adopting micro-irrigation.",
                "apply": "https://pmksy.gov.in",
                "helpline": "State Agriculture Office"
            }
        ],

        "soil": [
            {
                "name": "Soil Health Card Scheme",
                "description": "Free soil testing & fertilizer recommendation.",
                "eligibility": "All farmers.",
                "apply": "https://soilhealth.dac.gov.in",
                "helpline": "Agriculture Dept."
            }
        ],

        "organic": [
            {
                "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
                "description": "Support for organic farming clusters.",
                "eligibility": "Farmers shifting to organic farming.",
                "apply": "https://pgsindia-ncof.gov.in",
                "helpline": "Organic Farming Division"
            }
        ],

        "fisheries": [
            {
                "name": "Pradhan Mantri Matsya Sampada Yojana",
                "description": "Financial support for fisheries sector.",
                "eligibility": "Fish farmers.",
                "apply": "https://dof.gov.in/pmmsy",
                "helpline": "Fisheries Dept."
            }
        ]

    }

    if category in schemes:
        return jsonify(schemes[category])
    else:
        all_schemes = []
        for key in schemes:
            all_schemes.extend(schemes[key])
        return jsonify(all_schemes)

@app.route("/get_crop_calendar")
def get_crop_calendar():
    # ================== EXTENDED CROP CALENDAR ==================

    crop_calendar = {

        "Tomato": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "NPK 19:19:19 after 20 days, Urea at flowering",
                "irrigation": "Every 3–4 days",
                "harvest": "75–85 days"
            },
            "Rabi": {
                "sowing": "October – November",
                "fertilizer": "DAP at sowing, Urea after 25 days",
                "irrigation": "Every 5 days",
                "harvest": "80–90 days"
            }
        },

        "Paddy": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "NPK 20:10:10 after transplanting",
                "irrigation": "Maintain 2–5 cm standing water",
                "harvest": "110–120 days"
            },
            "Rabi": {
                "sowing": "November – December",
                "fertilizer": "Apply Urea in 3 split doses",
                "irrigation": "Alternate wetting and drying",
                "harvest": "120–130 days"
            }
        },

        "Maize": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "Apply Urea at 25 days",
                "irrigation": "Every 7–10 days",
                "harvest": "90–100 days"
            },
            "Rabi": {
                "sowing": "October – November",
                "fertilizer": "Apply NPK 20:20:0",
                "irrigation": "Every 8 days",
                "harvest": "100–110 days"
            }
        },

        "Wheat": {
            "Rabi": {
                "sowing": "November – December",
                "fertilizer": "Apply DAP at sowing, Urea after 30 days",
                "irrigation": "Every 15–20 days",
                "harvest": "120–140 days"
            }
        },

        "Cotton": {
            "Kharif": {
                "sowing": "May – June",
                "fertilizer": "NPK 20:10:10 at early growth",
                "irrigation": "Every 7 days",
                "harvest": "150–180 days"
            }
        },

        "Sugarcane": {
            "Summer": {
                "sowing": "January – March",
                "fertilizer": "Apply Urea every 45 days",
                "irrigation": "Every 10–12 days",
                "harvest": "10–12 months"
            }
        },

        "Onion": {
            "Rabi": {
                "sowing": "October – November",
                "fertilizer": "Apply DAP at sowing",
                "irrigation": "Every 5–6 days",
                "harvest": "90–100 days"
            }
        },

        "Groundnut": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "Apply Gypsum at flowering stage",
                "irrigation": "Every 7 days",
                "harvest": "100–110 days"
            }
        },

        "Soybean": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "Apply NPK 12:32:16 at sowing",
                "irrigation": "Only if dry spell",
                "harvest": "100–110 days"
            }
        },

        "Chilli": {
            "Kharif": {
                "sowing": "June – July",
                "fertilizer": "Apply NPK 20:20:20 every 20 days",
                "irrigation": "Every 4–5 days",
                "harvest": "90–120 days"
            }
        }
    }

    crop = request.args.get("crop")
    season = request.args.get("season")

    for c in crop_calendar:
        if c.lower() == crop.lower():
            for s in crop_calendar[c]:
                if s.lower() == season.lower():
                    return jsonify(crop_calendar[c][s])

    return jsonify({"error": "Data not found"})
# ================== HOME PAGE ==================
@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bharat Farming Assistant AI</title>

    <style>
    body{margin:0;font-family:Segoe UI;
    background:url('https://images.unsplash.com/photo-1500382017468-9049fed747ef') no-repeat center center;
    background-size:cover;background-attachment:fixed;
    min-height:100vh;overflow-y:auto;}

    .overlay{background:rgba(0,0,0,0.5);min-height:100vh}

    .header{height:60px;background:#2E7D32;color:white;
    display:flex;align-items:center;justify-content:space-between;
    padding:0 20px;font-weight:bold}

    .sidebar{position:fixed;top:60px;left:-250px;width:230px;height:100%;
    background:#1B5E20;color:white;transition:0.3s;padding-top:10px;z-index:999}
    .sidebar.active{left:0}
    .sidebar div{padding:14px 20px;cursor:pointer}
    .sidebar div:hover{background:#2E7D32}

    .content{margin-top:20px;padding:20px;color:white;height:75vh;overflow:auto}

    .feature-box{background:rgba(0,0,0,0.6);
    padding:20px;border-radius:12px;margin-bottom:15px}

    /* AI CHAT */
    #fab{
    position:fixed;bottom:20px;right:20px;
    width:60px;height:60px;background:#2E7D32;
    border-radius:50%;display:flex;align-items:center;
    justify-content:center;color:white;font-size:26px;
    cursor:pointer;z-index:9999;
    }

    #chatbox{
    position:fixed;bottom:90px;right:20px;
    width:360px;height:480px;background:white;
    border-radius:15px;display:none;
    flex-direction:column;overflow:hidden;
    box-shadow:0 5px 15px rgba(0,0,0,0.4);
    z-index:9999;
    }

    .chat-header{
    background:#2E7D32;color:white;padding:10px;
    }

    .messages{
    flex:1;padding:10px;overflow:auto;font-size:14px;
    }

    .input-area{
    display:flex;padding:5px;border-top:1px solid #ccc;
    gap:4px;
    }

    input{
    flex:1;padding:8px;border-radius:20px;border:1px solid #ccc;
    }

    button{
    background:#2E7D32;color:white;border:none;
    border-radius:20px;padding:6px 10px;cursor:pointer;
    }
    </style>
    </head>

    <body>
    <div class="overlay">

    <div class="header">
    <div id="menuBtn" onclick="toggleMenu()" style="cursor:pointer">☰</div>
    <div>Bharat Farming Assistant AI 🌾</div>
    <div><span id="weather">Loading...</span></div>
    </div>

    <div class="sidebar" id="sidebar">
    <div onclick="loadMarket()">🏪 Market Prices</div>
    <div onclick="loadIrrigation()">💧 Irrigation Advice</div>
    <div onclick="loadFertilizer()">🧪 Fertilizer Guide</div>
    <div onclick="loadSchemes()">🏛 Government Schemes</div>
    <div onclick="loadCropCalendar()">📅 Crop Calendar</div>
    <div onclick="loadYieldEstimator()">📈 Yield Estimator</div>
    <div onclick="loadSoilGuide()">🌍 Soil Health Guide</div>
    <div onclick="loadExpenseTracker()">💰 Expense Tracker</div>
    </div>

    <div class="content" id="dashboard">
    <h2>🌾 Smart Farming Dashboard</h2>
    </div>

    </div>

    <!-- AI Floating Button -->
    <div id="fab" onclick="toggleChat()">🤖</div>

    <!-- AI Chat Box -->
    <div id="chatbox">
    <div class="chat-header">AI Assistant 🎙</div>

    <select id="language" style="margin:5px;">
    <option>English</option>
    <option>Hindi</option>
    <option>Kannada</option>
    </select>

    <div class="messages" id="messages"></div>

    <div class="input-area">
    <input id="message" placeholder="Ask farming question...">
    <button onclick="startVoice()">🎤</button>
    <button onclick="sendMessage()">Send</button>
    <button onclick="stopSpeech()">⛔</button>
    </div>
    </div>

    <script>

    function toggleMenu(){
    document.getElementById("sidebar").classList.toggle("active")
    }

    document.addEventListener("click", function(event){
    let sidebar = document.getElementById("sidebar");
    let toggleBtn = document.getElementById("menuBtn");
    if(sidebar.classList.contains("active")){
    if(!sidebar.contains(event.target) &&
       !toggleBtn.contains(event.target)){
    sidebar.classList.remove("active");
    }}});

    function toggleChat(){
    let chat=document.getElementById("chatbox");
    chat.style.display = chat.style.display==="flex" ? "none" : "flex";
    }

    /* WEATHER */
    async function loadWeather(){
    let res=await fetch("/get_weather");
    let data=await res.json();
    if(!data.error){
    document.getElementById("weather").innerText=
    data.city+" | "+data.temp+"°C | "+data.spray;
    }}
    loadWeather();

    /* SEND MESSAGE WITH TYPING */
    async function sendMessage(){
    let msg=document.getElementById("message").value;
    if(!msg) return;

    let language=document.getElementById("language").value;
    let messages=document.getElementById("messages");

    messages.innerHTML += "<div><b>You:</b> "+msg+"</div>";
    document.getElementById("message").value="";

    messages.innerHTML += "<div id='typing'><i>AI is typing...</i></div>";
    messages.scrollTop=messages.scrollHeight;

    let res=await fetch("/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:msg,language:language})
    });
    let data=await res.json();

    document.getElementById("typing").remove();

    messages.innerHTML += "<div style='background:#E8F5E9;padding:6px;margin:4px;border-radius:10px;'><b>AI:</b> "+data.reply+"</div>";
    messages.scrollTop=messages.scrollHeight;

    window.speechSynthesis.cancel();
    let speech=new SpeechSynthesisUtterance(data.reply);
    speech.lang = language==="Hindi" ? "hi-IN" :
                  language==="Kannada" ? "kn-IN" : "en-IN";
    window.speechSynthesis.speak(speech);
    }

    function stopSpeech(){
    window.speechSynthesis.cancel();
    }

    /* MIC INPUT */
    function startVoice(){
    if(!('webkitSpeechRecognition' in window) &&
       !('SpeechRecognition' in window)){
    alert("Use Chrome browser for mic.");
    return;
    }

    let SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

    let recognition = new SpeechRecognition();
    let language=document.getElementById("language").value;

    recognition.lang =
    language==="Hindi" ? "hi-IN" :
    language==="Kannada" ? "kn-IN" : "en-IN";

    recognition.start();

    recognition.onresult = function(event){
    document.getElementById("message").value =
    event.results[0][0].transcript;
    };
    }
   async function loadMarket(){

let dash=document.getElementById("dashboard");

dash.innerHTML=`
<div class="feature-box">
<h2>📊 Karnataka Mandi Prices</h2>

<input id="cropName" placeholder="Enter Crop (e.g. Tomato)"><br><br>

<select id="districtSelect"></select><br><br>

<button onclick="fetchMandi()">Search</button>

<div id="mandiResult"></div>
</div>`;

// Load Karnataka districts
let res = await fetch("/get_karnataka_districts");
let districts = await res.json();

let districtSelect = document.getElementById("districtSelect");
districtSelect.innerHTML = "<option value=''>All Districts</option>";

districts.forEach(d=>{
districtSelect.innerHTML += `<option value="${d}">${d}</option>`;
});
}
async function fetchMandi(){

let crop=document.getElementById("cropName").value;
let district=document.getElementById("districtSelect").value;

let url="/get_mandi?";

if(crop) url+="crop="+encodeURIComponent(crop)+"&";
if(district) url+="district="+encodeURIComponent(district);

let res=await fetch(url);
let data=await res.json();

let html="";

if(data.length===0){
html="<div style='color:red;margin-top:10px;'>No data found</div>";
}else{
data.forEach(item=>{
html+=`
<div style="background:#1B5E20;padding:10px;margin:8px;border-radius:8px;color:white;">
<b>${item.commodity}</b><br>
Market: ${item.market}<br>
District: ${item.district}<br>
Min: ₹${item.min_price} |
Max: ₹${item.max_price} |
Modal: ₹${item.modal_price}
</div>`;
});
}

document.getElementById("mandiResult").innerHTML=html;
}
 async function loadIrrigation(){

let dash=document.getElementById("dashboard");

dash.innerHTML=`
<div class="feature-box">
<h2>💧 Smart Irrigation Advice</h2>
<input id="cropType" placeholder="Enter crop name"><br><br>
<button onclick="getIrrigation()">Get Advice</button>
<div id="irrigationResult"></div>
</div>`;
}

async function getIrrigation(){

let crop=document.getElementById("cropType").value || "General";

let weather=await fetch("/get_weather");
let wdata=await weather.json();

let res=await fetch("/irrigation_advice?crop="+crop+
"&temp="+wdata.temp+
"&humidity="+wdata.humidity);

let data=await res.json();

document.getElementById("irrigationResult").innerHTML=
"<div style='margin-top:15px;background:#1B5E20;padding:10px;border-radius:8px;color:white;'>"
+ data.advice +
"</div>";
}
function loadFertilizer(){

let dash=document.getElementById("dashboard");

dash.innerHTML=`
<div class="feature-box">
<h2>🧪 Fertilizer Recommendation</h2>

<select id="cropSelect">
<option value="rice">Rice</option>
<option value="wheat">Wheat</option>
<option value="maize">Maize</option>
<option value="cotton">Cotton</option>
<option value="tomato">Tomato</option>
<option value="Sugarcane">Sugarcane</option>
<option value="Potato">Potato</option>
<option value="Onion">Onion</option>
<option value="Chilli">Chilli</option>
<option value="Banana">Banana</option>
<option value="Groundnut">Groundnut</option>
<option value="Soybean">Soybean</option>
<option value="Pigeonpea">Pigeonpea</option>

</select><br><br>

<select id="stageSelect">
<option value="early">Early Stage</option>
<option value="mid">Mid Stage</option>
<option value="late">Late Stage</option>
</select><br><br>

<select id="langSelect">
<option>English</option>
<option>Hindi</option>
<option>Kannada</option>
</select><br><br>

<button onclick="getFertilizer()">Get Recommendation</button>

<div id="fertilizerResult"></div>
</div>`;
}
async function getFertilizer(){

let crop=document.getElementById("cropSelect").value;
let stage=document.getElementById("stageSelect").value;
let lang=document.getElementById("langSelect").value;

let res=await fetch(
"/fertilizer_advice?crop="+crop+
"&stage="+stage+
"&lang="+lang
);

let data=await res.json();

document.getElementById("fertilizerResult").innerHTML=
"<div style='margin-top:15px;background:#1B5E20;padding:10px;border-radius:8px;color:white;'>"
+ data.recommendation +
"</div>";

}
// ================== LOAD GOV SCHEMES UI ==================
function loadSchemes(){

let dash = document.getElementById("dashboard");

dash.innerHTML = `
<div class="feature-box">
<h2>🏛 Government Schemes</h2>


<select id="schemeCategory">
<option value="">All Schemes</option>
<option value="income">Income</option>
<option value="insurance">Insurance</option>
<option value="loan">Loan</option>
<option value="subsidy">Subsidy</option>
<option value="irrigation">Irrigation</option>
<option value="soil">Soil</option>
<option value="organic">Organic</option>
<option value="fisheries">Fisheries</option>
</select><br><br>

<button onclick="fetchSchemes()">Search</button>

<div id="schemeResult"></div>
</div>`;
}
async function fetchSchemes(){

let category = document.getElementById("schemeCategory").value;

let res = await fetch("/get_schemes?category=" + category);
let data = await res.json();

let html = "";

data.forEach(s=>{
html += `
<div class="scheme-card"
style="background:#1B5E20;padding:12px;margin:10px;border-radius:8px;color:white;">
<b style="font-size:16px;">${s.name}</b><br><br>
${s.description}<br><br>

<b>Eligibility:</b> ${s.eligibility}<br>
<b>Helpline:</b> ${s.helpline}<br><br>

<a href="${s.apply}" 
target="_blank" 
style="color:yellow;font-weight:bold;">
Apply / View Details
</a>
</div>`;
});

document.getElementById("schemeResult").innerHTML = html;

}
function loadCropCalendar(){

let dash = document.getElementById("dashboard");

dash.innerHTML = `
<div class="feature-box">
<h2>📅 Crop Calendar</h2>

<select id="cropSelect" onchange="updateSeasonOptions()">
<option>Tomato</option>
<option>Paddy</option>
<option>Maize</option>
<option>Wheat</option>
<option>Cotton</option>
<option>Sugarcane</option>
<option>Onion</option>
<option>Groundnut</option>
<option>Soybean</option>
<option>Chilli</option>
</select>

<select id="seasonSelect"></select>

<button onclick="fetchCalendar()">Show</button>

<div id="calendarResult" style="margin-top:15px;"></div>

</div>`;

updateSeasonOptions(); // Load season initially
}
function updateSeasonOptions(){

let crop = document.getElementById("cropSelect").value;
let seasonSelect = document.getElementById("seasonSelect");

let seasonMap = {
"Tomato": ["Kharif", "Rabi"],
"Paddy": ["Kharif", "Rabi"],
"Maize": ["Kharif", "Rabi"],
"Wheat": ["Rabi"],
"Cotton": ["Kharif"],
"Sugarcane": ["Summer"],
"Onion": ["Rabi"],
"Groundnut": ["Kharif"],
"Soybean": ["Kharif"],
"Chilli": ["Kharif"]
};

seasonSelect.innerHTML = "";

seasonMap[crop].forEach(season => {
seasonSelect.innerHTML += `<option>${season}</option>`;
});
}
async function fetchCalendar(){

let crop = document.getElementById("cropSelect").value;
let season = document.getElementById("seasonSelect").value;

let res = await fetch(`/get_crop_calendar?crop=${crop}&season=${season}`);
let data = await res.json();

let box = document.getElementById("calendarResult");

if(data.error){
box.innerHTML = "<span style='color:red'>No data found</span>";
return;
}

box.innerHTML = `
<div style="background:#1B5E20;padding:12px;border-radius:10px;color:white;">
<b>🌱 Sowing:</b> ${data.sowing}<br><br>
<b>🧪 Fertilizer:</b> ${data.fertilizer}<br><br>
<b>💧 Irrigation:</b> ${data.irrigation}<br><br>
<b>🌾 Harvest:</b> ${data.harvest}
</div>
`;
}

function loadYieldEstimator(){

let dash = document.getElementById("dashboard");

dash.innerHTML = `
<div class="feature-box">
<h2>📈 Yield Estimator</h2>

<input type="text" id="cropName" placeholder="Enter Crop"><br><br>

<input type="number" id="landArea" placeholder="Land (in Acres)"><br><br>

<input type="number" id="yieldPerAcre" placeholder="Yield per Acre (Quintal)"><br><br>

<input type="number" id="marketPrice" placeholder="Market Price per Quintal (₹)"><br><br>

<button onclick="calculateYield()">Calculate</button>

<div id="yieldResult" style="margin-top:15px;"></div>

</div>`;
}

function calculateYield(){

let crop = document.getElementById("cropName").value;
let land = parseFloat(document.getElementById("landArea").value);
let yieldPerAcre = parseFloat(document.getElementById("yieldPerAcre").value);
let price = parseFloat(document.getElementById("marketPrice").value);

if(!land || !yieldPerAcre || !price){
alert("Please fill all fields");
return;
}

let totalProduction = land * yieldPerAcre;
let totalIncome = totalProduction * price;

document.getElementById("yieldResult").innerHTML = `
<div style="background:#1B5E20;padding:12px;border-radius:10px;color:white;">
<b>🌾 Crop:</b> ${crop}<br><br>
<b>Total Production:</b> ${totalProduction.toFixed(2)} Quintals<br><br>
<b>Estimated Income:</b> ₹ ${totalIncome.toLocaleString()}
</div>
`;
}
function loadSoilGuide(){

let dash = document.getElementById("dashboard");

dash.innerHTML = `
<div class="feature-box">
<h2>🌍 Soil Health Guide</h2>

<select id="soilSelect" onchange="showSoilInfo()">
<option value="">Select Soil Type</option>
<option value="black">Black Soil</option>
<option value="red">Red Soil</option>
<option value="sandy">Sandy Soil</option>
<option value="laterite">Laterite Soil</option>
<option value="alluvial">Alluvial Soil</option>
</select>

<div id="soilResult" style="margin-top:15px;"></div>

</div>`;
}
function showSoilInfo(){

let soil = document.getElementById("soilSelect").value;

let soilData = {

black: {
crops: "Cotton, Soybean, Jowar, Tur",
fertilizer: "NPK 20:10:10, Add Zinc if deficiency",
organic: "Add compost yearly, Maintain drainage"
},

red: {
crops: "Groundnut, Millets, Pulses",
fertilizer: "NPK 15:15:15, Add Lime if acidic",
organic: "Add farmyard manure regularly"
},

sandy: {
crops: "Watermelon, Groundnut, Coconut",
fertilizer: "Frequent small nitrogen doses",
organic: "Add compost to increase water retention"
},

laterite: {
crops: "Tea, Coffee, Cashew",
fertilizer: "Apply Potash-rich fertilizers",
organic: "Add organic matter to improve fertility"
},

alluvial: {
crops: "Wheat, Rice, Sugarcane, Maize",
fertilizer: "Balanced NPK 20:20:20",
organic: "Use green manure and vermicompost"
}
};

let box = document.getElementById("soilResult");

if(!soil){
box.innerHTML = "";
return;
}

let data = soilData[soil];

box.innerHTML = `
<div style="background:#1B5E20;padding:12px;border-radius:10px;color:white;">
<b>🌾 Suitable Crops:</b> ${data.crops}<br><br>
<b>🧪 Fertilizer Recommendation:</b> ${data.fertilizer}<br><br>
<b>🌱 Organic Improvement:</b> ${data.organic}
</div>
`;
}
function loadExpenseTracker(){

let dash = document.getElementById("dashboard");

dash.innerHTML = `
<div class="feature-box">
<h2>💰 Expense & Profit Calculator</h2>

<input type="number" id="seedCost" placeholder="Seed Cost (₹)"><br><br>
<input type="number" id="fertilizerCost" placeholder="Fertilizer Cost (₹)"><br><br>
<input type="number" id="pesticideCost" placeholder="Pesticide Cost (₹)"><br><br>
<input type="number" id="labourCost" placeholder="Labour Cost (₹)"><br><br>
<input type="number" id="transportCost" placeholder="Transport Cost (₹)"><br><br>

<hr>

<input type="number" id="totalIncome" placeholder="Total Income (₹)"><br><br>

<button onclick="calculateProfit()">Calculate Profit</button>

<div id="profitResult" style="margin-top:15px;"></div>

</div>`;
}
function calculateProfit(){

let seed = parseFloat(document.getElementById("seedCost").value) || 0;
let fertilizer = parseFloat(document.getElementById("fertilizerCost").value) || 0;
let pesticide = parseFloat(document.getElementById("pesticideCost").value) || 0;
let labour = parseFloat(document.getElementById("labourCost").value) || 0;
let transport = parseFloat(document.getElementById("transportCost").value) || 0;
let income = parseFloat(document.getElementById("totalIncome").value) || 0;

let totalExpense = seed + fertilizer + pesticide + labour + transport;
let netProfit = income - totalExpense;

let color = netProfit >= 0 ? "green" : "red";
let status = netProfit >= 0 ? "Profit" : "Loss";

document.getElementById("profitResult").innerHTML = `
<div style="background:#1B5E20;padding:12px;border-radius:10px;color:white;">
<b>Total Investment:</b> ₹ ${totalExpense.toLocaleString()}<br><br>
<b>${status}:</b> <span style="color:${color}; font-weight:bold;">
₹ ${netProfit.toLocaleString()}
</span>
</div>
`;
}
    </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
