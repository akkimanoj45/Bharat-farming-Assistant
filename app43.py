from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import requests

app = Flask(__name__)

# =============== PUT YOUR KEYS ===============
GROQ_API_KEY = "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"
WEATHER_API_KEY = "2b46ee663df58c9c5289e6a614005e10"

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Bharat Farming Assistant AI.
Help Indian farmers in simple practical language.
Reply strictly in selected language.
Warn before spraying if rain or humidity is high.
"""

# ================= WEATHER =================
@app.route("/get_weather")
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Bijapur&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return jsonify({"error": "Weather API error"})

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["main"]
        city = data["name"]

        spray_alert = "Safe to Spray ✅"
        if "Rain" in condition or humidity > 80:
            spray_alert = "Do NOT Spray ❌"

        return jsonify({
            "temp": temp,
            "spray": spray_alert,
            "city": city
        })

    except:
        return jsonify({"error": "Weather error"})

# ================= AI CHAT =================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")
    language = data.get("language", "English")

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Reply strictly in {language} language."},
                {"role": "user", "content": message}
            ],
        )

        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "AI error: " + str(e)})

# ================= HOME =================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bharat Farming Assistant AI</title>

<style>
body{
margin:0;font-family:Segoe UI;
background:url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854')no-repeat center/cover;
height:100vh;overflow:hidden}
.overlay{background:rgba(0,0,0,0.4);height:100vh}

/* Header */
.header{
height:60px;background:#2E7D32;color:white;
display:flex;align-items:center;justify-content:space-between;padding:0 20px}

/* Layout */
.container{display:flex;height:calc(100vh - 60px)}

/* Sidebar */
.sidebar{
width:250px;background:#1B5E20;color:white;padding:15px}

/* Farmer Profile Card */
.profile-card{
background:linear-gradient(135deg,#43A047,#2E7D32);
padding:15px;border-radius:15px;margin-bottom:20px;
text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.3)}
.profile-avatar{
width:70px;height:70px;border-radius:50%;
background:white;margin:0 auto 10px auto;
display:flex;align-items:center;justify-content:center;
font-size:30px;color:#2E7D32;font-weight:bold}
.profile-name{font-size:16px;font-weight:bold}
.profile-location{font-size:13px;opacity:0.9}

/* Sidebar items */
.sidebar div.menu-item{
padding:12px 15px;margin:5px 0;
border-radius:10px;cursor:pointer}
.sidebar div.menu-item:hover{
background:#2E7D32}

/* Content */
.content{flex:1;padding:20px;color:white}

/* Floating AI */
.fab{
position:fixed;bottom:20px;right:20px;width:65px;height:65px;
background:#2E7D32;border-radius:50%;display:flex;
align-items:center;justify-content:center;
color:white;font-size:28px;cursor:pointer}

/* Chat */
.chatbox{
position:fixed;bottom:100px;right:20px;width:340px;height:520px;
background:white;border-radius:20px;display:none;flex-direction:column}
.chat-header{background:#2E7D32;color:white;padding:12px;border-radius:20px 20px 0 0}
.messages{flex:1;padding:10px;overflow:auto;font-size:14px}
.input-area{display:flex;border-top:1px solid #ddd}
input{flex:1;padding:10px;border:none}
button{background:#2E7D32;color:white;border:none;padding:10px;cursor:pointer}
select{width:100%;padding:6px;border:none}
</style>
</head>

<body>
<div class="overlay">

<div class="header">
<div>Bharat Farming Assistant AI 🌾</div>
<div><span id="time"></span> | <span id="weather">Loading...</span></div>
</div>

<div class="container">

<div class="sidebar">

<div class="profile-card">
<div class="profile-avatar">👨‍🌾</div>
<div class="profile-name">Farmer Ramesh</div>
<div class="profile-location">Bijapur, Karnataka</div>
</div>

<div class="menu-item">🌱 Disease Detection</div>
<div class="menu-item">🌦 Weather</div>
<div class="menu-item">💧 Irrigation</div>
<div class="menu-item">🧪 Fertilizer</div>
<div class="menu-item">📈 Yield</div>
<div class="menu-item">🏪 Market</div>
<div class="menu-item">🏛 Schemes</div>

</div>

<div class="content">
<h2>🌾 Smart Farming Dashboard</h2>
<p>Select a feature from left panel.</p>
</div>

</div>

</div>

<div class="fab" onclick="toggleChat()">🤖</div>

<div class="chatbox" id="chatbox">
<div class="chat-header">AI Assistant 🎙</div>

<select id="language">
<option>English</option>
<option>Hindi</option>
<option>Kannada</option>
</select>

<div class="messages" id="messages"></div>

<div class="input-area">
<input id="message" placeholder="Ask farming question...">
<button onclick="startVoice()">🎙</button>
<button onclick="sendMessage()">Send</button>
</div>
</div>

<script>
function toggleChat(){
let c=document.getElementById("chatbox");
c.style.display=c.style.display==="flex"?"none":"flex"}

/* AI */
async function sendMessage(){
let msg=document.getElementById("message").value;
if(!msg)return;
let language=document.getElementById("language").value;

document.getElementById("messages").innerHTML+="<p><b>You:</b>"+msg+"</p>";
document.getElementById("message").value="";

let res=await fetch("/chat",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,language:language})});

let data=await res.json();
document.getElementById("messages").innerHTML+="<p><b>AI:</b>"+data.reply+"</p>";

let speech=new SpeechSynthesisUtterance(data.reply);
if(language==="Hindi") speech.lang="hi-IN";
else if(language==="Kannada") speech.lang="kn-IN";
else speech.lang="en-IN";

speechSynthesis.speak(speech);
}

function startVoice(){
let language=document.getElementById("language").value;
let rec=new(window.SpeechRecognition||window.webkitSpeechRecognition)();
rec.lang = language==="Hindi"?"hi-IN":language==="Kannada"?"kn-IN":"en-IN";
rec.start();
rec.onresult=function(e){
document.getElementById("message").value=e.results[0][0].transcript};
}

/* Clock */
setInterval(()=>{document.getElementById("time").innerText=
new Date().toLocaleTimeString()},1000);

/* Weather */
async function loadWeather(){
try{
let res=await fetch("/get_weather");
let data=await res.json();
if(data.error){
document.getElementById("weather").innerText="Weather unavailable";
}else{
document.getElementById("weather").innerText=
data.city+" | "+data.temp+"°C | "+data.spray;
}
}catch{
document.getElementById("weather").innerText="Weather offline";
}
}
loadWeather();
</script>

</body>
</html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)