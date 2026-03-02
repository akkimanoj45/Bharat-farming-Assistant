import os
import json
import base64
import requests
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bharat-farming-secret-2024")


GROQ_API_KEY = os.environ.get("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", "")
OPENWEATHER_API_KEY = os.environ.get("2b46ee663df58c9c5289e6a614005e10", "")
PLANT_ID_API_KEY = os.environ.get("br5ST4mufFHuAo6Il7SHONAUfbvtGaLhyXY1xZgVmYdyWjenSN", "")
DATA_GOV_API_KEY = os.environ.get("579b464db66ec23bdd00000161d7e9b7b5dc4cb45006f93ed3bc01f2", "")


GOVERNMENT_SCHEMES = [
    {
        "category": "Income Support",
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "description": "Direct income support of Rs 6,000 per year to small and marginal farmers, paid in three equal installments.",
        "eligibility": "All landholding farmer families with cultivable land, subject to exclusion criteria.",
        "apply_link": "https://pmkisan.gov.in/",
        "helpline": "155261 / 1800115526"
    },
    {
        "category": "Insurance",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "description": "Comprehensive crop insurance covering pre-sowing to post-harvest losses due to natural calamities, pests and diseases.",
        "eligibility": "All farmers including sharecroppers and tenant farmers growing notified crops.",
        "apply_link": "https://pmfby.gov.in/",
        "helpline": "1800 200 7710"
    },
    {
        "category": "Loan",
        "name": "Kisan Credit Card (KCC) Scheme",
        "description": "Short-term credit needs for crop cultivation, post-harvest expenses, allied activities at subsidized interest rates.",
        "eligibility": "Farmers, sharecroppers, oral lessees, self-help groups and joint liability groups.",
        "apply_link": "https://www.nabard.org/content.aspx?id=572",
        "helpline": "1800 200 0027"
    },
    {
        "category": "Subsidy",
        "name": "PM Krishi Sinchayee Yojana (PMKSY)",
        "description": "'Har Khet Ko Pani' and 'More Crop Per Drop' – promotes water use efficiency with micro-irrigation subsidies up to 55% for small/marginal farmers.",
        "eligibility": "All farmers. Small & marginal farmers get additional 10% top-up subsidy.",
        "apply_link": "https://pmksy.gov.in/",
        "helpline": "1800 180 1551"
    },
    {
        "category": "Irrigation",
        "name": "Rashtriya Krishi Vikas Yojana (RKVY)",
        "description": "Strengthens agricultural infrastructure including irrigation, storage, and market linkages through state-specific plans.",
        "eligibility": "State governments implement; farmers benefit through state-run programs.",
        "apply_link": "https://rkvy.nic.in/",
        "helpline": "011-23382651"
    },
    {
        "category": "Soil",
        "name": "Soil Health Card Scheme",
        "description": "Provides farmers with soil health cards containing information on nutrient status and recommendations for fertilizer use.",
        "eligibility": "All farmers across India.",
        "apply_link": "https://soilhealth.dac.gov.in/",
        "helpline": "1800 180 1551"
    },
    {
        "category": "Organic",
        "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
        "description": "Promotes organic farming through cluster-based approach, providing Rs 50,000/ha over 3 years for inputs, certification and marketing.",
        "eligibility": "Farmers forming clusters of 50 acres minimum. Priority to small/marginal farmers.",
        "apply_link": "https://pgsindia-ncof.gov.in/pkvy/index.aspx",
        "helpline": "1800 180 1551"
    },
    {
        "category": "Fisheries",
        "name": "Pradhan Mantri Matsya Sampada Yojana (PMMSY)",
        "description": "Enhances fish production, improves infrastructure, modernizes fishing villages with subsidy up to 60% for SC/ST/women.",
        "eligibility": "Fishers, fish farmers, fish workers, fish vendors, SHGs, fishing cooperatives.",
        "apply_link": "https://pmmsy.dof.gov.in/",
        "helpline": "1800 425 1660"
    }
]

SOIL_DATA = {
    "Alluvial Soil": {
        "suitable_crops": ["Wheat", "Rice", "Sugarcane", "Cotton", "Jute", "Maize", "Vegetables"],
        "fertilizer": "Balanced NPK (Nitrogen-Phosphorus-Potassium). Moderately fertile – supplement with urea and DAP.",
        "organic_improvement": "Add green manure (dhaincha), compost, and farmyard manure to improve water retention and microbial activity."
    },
    "Black Cotton Soil": {
        "suitable_crops": ["Cotton", "Soybean", "Jowar", "Wheat", "Groundnut", "Sunflower", "Chickpea"],
        "fertilizer": "High in calcium and magnesium. Apply phosphorus and nitrogen. Avoid excess potassium.",
        "organic_improvement": "Add organic matter and gypsum to improve drainage and reduce cracking. Use cover crops like cowpea."
    },
    "Red Soil": {
        "suitable_crops": ["Groundnut", "Millets", "Tobacco", "Potato", "Maize", "Pulses", "Oilseeds"],
        "fertilizer": "Deficient in nitrogen, phosphorus, and organic matter. Apply heavy doses of compost with NPK fertilizers.",
        "organic_improvement": "Regular addition of green manure, vermicompost, and farmyard manure to improve fertility and water holding capacity."
    },
    "Laterite Soil": {
        "suitable_crops": ["Tea", "Coffee", "Rubber", "Cashew", "Tapioca", "Coconut", "Pineapple"],
        "fertilizer": "Poor in nitrogen and organic matter. Apply lime to reduce acidity. Use heavy NPK fertilization.",
        "organic_improvement": "Mulching with organic material, planting leguminous trees as shade, and using biofertilizers like Rhizobium."
    },
    "Sandy Soil": {
        "suitable_crops": ["Carrot", "Potato", "Peanut", "Watermelon", "Asparagus", "Radish", "Lettuce"],
        "fertilizer": "Very low in nutrients. Apply slow-release fertilizers frequently. Use liquid fertilizers for quick uptake.",
        "organic_improvement": "Add large quantities of compost, clay, and biochar to improve water and nutrient retention."
    },
    "Clay Soil": {
        "suitable_crops": ["Rice", "Wheat", "Sugarcane", "Broccoli", "Brussels Sprouts", "Cabbage", "Aster"],
        "fertilizer": "Rich in minerals but poor drainage. Apply gypsum to improve structure. Use slow-release NPK.",
        "organic_improvement": "Add coarse sand, organic matter, and practice deep plowing to break compaction and improve aeration."
    },
    "Loamy Soil": {
        "suitable_crops": ["Almost all crops", "Wheat", "Corn", "Tomatoes", "Peppers", "Strawberry", "Roses"],
        "fertilizer": "Well-balanced soil. Maintain fertility with standard NPK application based on soil test results.",
        "organic_improvement": "Maintain organic matter with regular compost additions. Ideal for most crops with minimal amendments needed."
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bharat Farming Assistant AI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #2E7D32;
            --primary-light: #4CAF50;
            --primary-dark: #1B5E20;
            --accent: #8BC34A;
            --gold: #FFC107;
            --bg-dark: rgba(0, 0, 0, 0.75);
            --bg-card: rgba(0, 20, 0, 0.7);
            --bg-sidebar: rgba(0, 30, 0, 0.85);
            --text-light: #E8F5E9;
            --text-muted: #A5D6A7;
            --border: rgba(76, 175, 80, 0.3);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a1a0a 0%, #1a2a0a 50%, #0a1a0a 100%);
            background-image:
                url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cpath d='M50 10 Q55 30 50 50 Q45 70 50 90' stroke='%23ffffff08' fill='none' stroke-width='1'/%3E%3Cpath d='M30 20 Q35 40 30 60 Q25 80 30 90' stroke='%23ffffff05' fill='none' stroke-width='1'/%3E%3Cpath d='M70 20 Q75 40 70 60 Q65 80 70 90' stroke='%23ffffff05' fill='none' stroke-width='1'/%3E%3C/svg%3E"),
                linear-gradient(135deg, #0a1a0a 0%, #1a2a0a 50%, #0a1a0a 100%);
            min-height: 100vh;
            color: var(--text-light);
            display: flex;
        }

        /* SIDEBAR */
        .sidebar {
            width: 260px;
            min-height: 100vh;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            position: fixed;
            left: 0; top: 0; bottom: 0;
            z-index: 100;
            transition: transform 0.3s ease;
            overflow-y: auto;
        }

        .sidebar-header {
            padding: 20px;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            text-align: center;
            border-bottom: 1px solid var(--border);
        }

        .sidebar-header .logo {
            font-size: 2.5rem;
            margin-bottom: 8px;
        }

        .sidebar-header h2 {
            font-size: 0.95rem;
            color: var(--accent);
            font-weight: 600;
            line-height: 1.3;
        }

        .sidebar-header p {
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .nav-section {
            padding: 12px 0;
        }

        .nav-section-title {
            font-size: 0.65rem;
            color: var(--text-muted);
            padding: 6px 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 20px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
            font-size: 0.87rem;
            color: var(--text-muted);
        }

        .nav-item:hover, .nav-item.active {
            background: rgba(76, 175, 80, 0.15);
            border-left-color: var(--primary-light);
            color: var(--text-light);
        }

        .nav-item i { width: 18px; text-align: center; font-size: 0.9rem; }

        /* MAIN CONTENT */
        .main {
            margin-left: 260px;
            flex: 1;
            padding: 24px;
            min-height: 100vh;
            transition: margin 0.3s ease;
        }

        .section {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        .section.active { display: block; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* CARDS */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(15px);
            box-shadow: var(--shadow);
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 1.2rem;
            color: var(--accent);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-header {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* FORMS */
        .form-group {
            margin-bottom: 16px;
        }

        label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        input, select, textarea {
            width: 100%;
            padding: 10px 14px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-light);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--primary-light);
        }

        select option { background: #1a2a1a; }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
        }

        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }

        .btn-secondary {
            background: rgba(76, 175, 80, 0.2);
            color: var(--accent);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover { background: rgba(76, 175, 80, 0.3); }

        .btn-danger {
            background: rgba(211, 47, 47, 0.8);
            color: white;
        }

        /* RESULT BOX */
        .result-box {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            margin-top: 16px;
            min-height: 60px;
            font-size: 0.9rem;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .result-box.loading { color: var(--text-muted); font-style: italic; }
        .result-box.error { border-color: #e57373; color: #ef9a9a; }

        /* CHAT */
        #chat-messages {
            height: 420px;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            border: 1px solid var(--border);
            margin-bottom: 12px;
        }

        .msg {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.88rem;
            line-height: 1.5;
            animation: fadeIn 0.2s ease;
        }

        .msg.user {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .msg.ai {
            background: rgba(30, 50, 30, 0.8);
            border: 1px solid var(--border);
            color: var(--text-light);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .chat-input-row {
            display: flex;
            gap: 8px;
        }

        .chat-input-row input { flex: 1; }

        /* WEATHER GRID */
        .weather-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }

        .weather-card {
            background: rgba(0,0,0,0.4);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }

        .weather-card .value {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--accent);
        }

        .weather-card .label {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .weather-card .icon { font-size: 1.8rem; margin-bottom: 6px; }

        /* MANDI CARDS */
        .mandi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }

        .mandi-card {
            background: rgba(0, 20, 0, 0.6);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
        }

        .mandi-card .mandi-name {
            font-weight: 600;
            color: var(--accent);
            font-size: 0.95rem;
        }

        .mandi-card .mandi-price {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--gold);
            margin: 6px 0;
        }

        .mandi-card .mandi-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* SCHEME CARDS */
        .scheme-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
        }

        .scheme-tab {
            padding: 6px 14px;
            border-radius: 20px;
            border: 1px solid var(--border);
            cursor: pointer;
            font-size: 0.82rem;
            color: var(--text-muted);
            background: rgba(0,0,0,0.3);
            transition: all 0.2s;
        }

        .scheme-tab:hover, .scheme-tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .scheme-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            background: rgba(0, 20, 0, 0.5);
            margin-bottom: 14px;
        }

        .scheme-category {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            background: var(--primary);
            color: white;
            margin-bottom: 10px;
        }

        .scheme-name {
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 8px;
        }

        .scheme-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px; }
        .scheme-elig { font-size: 0.82rem; color: #a5d6a7; margin-bottom: 10px; }

        .scheme-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .scheme-links a {
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            text-decoration: none;
            font-weight: 600;
        }

        .link-apply { background: var(--primary); color: white; }
        .link-helpline { background: rgba(255,193,7,0.2); color: var(--gold); border: 1px solid rgba(255,193,7,0.3); }

        /* CALCULATOR */
        .calc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }

        .calc-result {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin-top: 16px;
        }

        .calc-result-item {
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            border: 1px solid var(--border);
        }

        .calc-result-item .r-val {
            font-size: 1.4rem;
            font-weight: 700;
        }

        .calc-result-item .r-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .profit { color: #69f0ae; }
        .loss { color: #ef9a9a; }
        .neutral { color: var(--gold); }

        /* FLOATING CHAT BTN */
        .fab {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border: none;
            cursor: pointer;
            font-size: 1.4rem;
            color: white;
            box-shadow: 0 4px 20px rgba(46, 125, 50, 0.5);
            z-index: 200;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }

        .fab:hover { transform: scale(1.1); }

        /* MOBILE TOGGLE */
        .menu-toggle {
            display: none;
            position: fixed;
            top: 16px;
            left: 16px;
            z-index: 300;
            background: var(--primary);
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
        }

        .overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 99;
        }

        /* LOADING SPINNER */
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* BADGES */
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .badge-green { background: rgba(76,175,80,0.2); color: var(--accent); border: 1px solid rgba(76,175,80,0.3); }
        .badge-yellow { background: rgba(255,193,7,0.2); color: var(--gold); border: 1px solid rgba(255,193,7,0.3); }
        .badge-red { background: rgba(229,57,53,0.2); color: #ef9a9a; border: 1px solid rgba(229,57,53,0.3); }

        /* GRID LAYOUTS */
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }

        /* SOIL SECTION */
        .soil-info-item {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }

        .soil-info-item h4 {
            color: var(--accent);
            margin-bottom: 6px;
            font-size: 0.9rem;
        }

        .soil-info-item p {
            font-size: 0.84rem;
            color: var(--text-muted);
        }

        .crop-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
        }

        .crop-tag {
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            background: rgba(76,175,80,0.15);
            border: 1px solid rgba(76,175,80,0.3);
            color: var(--accent);
        }

        /* RESPONSIVE */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
            }
            .sidebar.open {
                transform: translateX(0);
            }
            .main {
                margin-left: 0;
                padding: 16px;
                padding-top: 60px;
            }
            .menu-toggle { display: block; }
            .overlay.show { display: block; }
            .two-col, .three-col { grid-template-columns: 1fr; }
            .calc-result { grid-template-columns: 1fr; }
            #chat-messages { height: 300px; }
        }

        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }

        /* PROGRESS BAR */
        .progress-bar {
            height: 8px;
            background: rgba(0,0,0,0.3);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 6px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        /* CALENDAR TABLE */
        .cal-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }

        .cal-table th {
            background: rgba(46,125,50,0.3);
            padding: 10px;
            text-align: left;
            font-size: 0.85rem;
            color: var(--accent);
        }

        .cal-table td {
            padding: 10px;
            border-bottom: 1px solid rgba(76,175,80,0.1);
            font-size: 0.85rem;
            color: var(--text-muted);
            vertical-align: top;
        }

        .cal-table tr:hover td { background: rgba(76,175,80,0.05); }

        /* UPLOAD AREA */
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }

        .upload-area:hover { border-color: var(--primary-light); background: rgba(76,175,80,0.05); }
        .upload-area.drag-over { border-color: var(--accent); background: rgba(76,175,80,0.1); }

        .upload-icon { font-size: 2.5rem; margin-bottom: 10px; }
        .upload-text { font-size: 0.9rem; color: var(--text-muted); }

        #disease-preview {
            max-width: 100%;
            max-height: 200px;
            border-radius: 10px;
            margin-top: 12px;
            display: none;
        }
    </style>
</head>
<body>

<button class="menu-toggle" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
<div class="overlay" id="overlay" onclick="closeSidebar()"></div>

<aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <div class="logo">🌾</div>
        <h2>Bharat Farming<br>Assistant AI</h2>
        <p>भारत कृषि सहायक</p>
    </div>

    <nav>
        <div class="nav-section">
            <div class="nav-section-title">AI Tools</div>
            <div class="nav-item active" onclick="showSection('chat')">
                <i class="fas fa-robot"></i> AI Chat Assistant
            </div>
            <div class="nav-item" onclick="showSection('disease')">
                <i class="fas fa-leaf"></i> Crop Disease Detection
            </div>
        </div>
        <div class="nav-section">
            <div class="nav-section-title">Field Intelligence</div>
            <div class="nav-item" onclick="showSection('weather')">
                <i class="fas fa-cloud-sun"></i> Weather Intelligence
            </div>
            <div class="nav-item" onclick="showSection('irrigation')">
                <i class="fas fa-tint"></i> Smart Irrigation
            </div>
            <div class="nav-item" onclick="showSection('fertilizer')">
                <i class="fas fa-flask"></i> Fertilizer Engine
            </div>
        </div>
        <div class="nav-section">
            <div class="nav-section-title">Market & Finance</div>
            <div class="nav-item" onclick="showSection('mandi')">
                <i class="fas fa-store"></i> Mandi Prices
            </div>
            <div class="nav-item" onclick="showSection('yield')">
                <i class="fas fa-calculator"></i> Yield Estimator
            </div>
            <div class="nav-item" onclick="showSection('expense')">
                <i class="fas fa-chart-pie"></i> Expense & Profit
            </div>
        </div>
        <div class="nav-section">
            <div class="nav-section-title">Knowledge</div>
            <div class="nav-item" onclick="showSection('schemes')">
                <i class="fas fa-landmark"></i> Govt Schemes
            </div>
            <div class="nav-item" onclick="showSection('calendar')">
                <i class="fas fa-calendar-alt"></i> Crop Calendar
            </div>
            <div class="nav-item" onclick="showSection('soil')">
                <i class="fas fa-seedling"></i> Soil Health Guide
            </div>
        </div>
    </nav>
</aside>

<main class="main">

    <!-- AI CHAT -->
    <div class="section active" id="sec-chat">
        <div class="section-header"><i class="fas fa-robot"></i> AI Chat Assistant</div>
        <div class="card">
            <div style="display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap;">
                <select id="chat-lang" style="width:auto; padding:8px 12px;">
                    <option value="en">English</option>
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="kn">Kannada (ಕನ್ನಡ)</option>
                </select>
                <span class="badge badge-green">Powered by Llama 3.3 70B</span>
            </div>
            <div id="chat-messages">
                <div class="msg ai">
                    🌾 Namaste! I am your Bharat Farming Assistant. Ask me anything about farming, crops, weather, diseases, or government schemes. I support English, Hindi, and Kannada!
                </div>
            </div>
            <div class="chat-input-row">
                <input type="text" id="chat-input" placeholder="Ask about crops, weather, diseases..." onkeydown="if(event.key==='Enter') sendChat()">
                <button class="btn btn-secondary" onclick="startVoice()" title="Voice Input"><i class="fas fa-microphone"></i></button>
                <button class="btn btn-primary" onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
            </div>
            <div style="margin-top:10px; display:flex; gap:8px; flex-wrap:wrap;">
                <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="ttsToggle()"><i class="fas fa-volume-up"></i> TTS</button>
                <button class="btn btn-secondary" style="font-size:0.75rem;" onclick="clearChat()"><i class="fas fa-trash"></i> Clear</button>
                <span id="voice-status" style="font-size:0.78rem; color:var(--text-muted); align-self:center;"></span>
            </div>
        </div>
    </div>

    <!-- DISEASE DETECTION -->
    <div class="section" id="sec-disease">
        <div class="section-header"><i class="fas fa-leaf"></i> Crop Disease Detection</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-upload"></i> Upload Plant Image</div>
                <div class="upload-area" id="upload-area" onclick="document.getElementById('disease-file').click()"
                     ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
                    <div class="upload-icon">🌿</div>
                    <div class="upload-text">Click or drag & drop a plant image<br><small>JPG, PNG supported</small></div>
                </div>
                <input type="file" id="disease-file" accept="image/*" style="display:none" onchange="previewImage(this)">
                <img id="disease-preview" alt="Plant preview">
                <div style="margin-top:14px; display:flex; gap:8px;">
                    <select id="disease-lang" style="flex:1;">
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="kn">Kannada</option>
                    </select>
                    <button class="btn btn-primary" onclick="detectDisease()"><i class="fas fa-search"></i> Analyze</button>
                </div>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-microscope"></i> Analysis Results</div>
                <div id="disease-result" class="result-box" style="min-height:200px;">Upload an image to get disease analysis.</div>
            </div>
        </div>
    </div>

    <!-- WEATHER -->
    <div class="section" id="sec-weather">
        <div class="section-header"><i class="fas fa-cloud-sun"></i> Weather Intelligence</div>
        <div class="card">
            <div class="card-title"><i class="fas fa-map-marker-alt"></i> Get Weather Data</div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <input type="text" id="weather-city" placeholder="Enter city name (e.g. Bengaluru)" style="flex:1;">
                <button class="btn btn-primary" onclick="getWeather()"><i class="fas fa-search"></i> Get Weather</button>
                <button class="btn btn-secondary" onclick="getWeatherGPS()"><i class="fas fa-location-arrow"></i> My Location</button>
            </div>
            <div id="weather-result"></div>
        </div>
    </div>

    <!-- IRRIGATION -->
    <div class="section" id="sec-irrigation">
        <div class="section-header"><i class="fas fa-tint"></i> Smart Irrigation Engine</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-seedling"></i> Irrigation Parameters</div>
                <div class="form-group">
                    <label>Crop Name</label>
                    <input type="text" id="irr-crop" placeholder="e.g. Rice, Wheat, Cotton">
                </div>
                <div class="form-group">
                    <label>Crop Growth Stage</label>
                    <select id="irr-stage">
                        <option>Germination</option>
                        <option>Seedling</option>
                        <option>Vegetative</option>
                        <option>Flowering</option>
                        <option>Fruiting / Pod Fill</option>
                        <option>Maturity / Harvest</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Soil Type</label>
                    <select id="irr-soil">
                        <option>Alluvial Soil</option>
                        <option>Black Cotton Soil</option>
                        <option>Red Soil</option>
                        <option>Sandy Soil</option>
                        <option>Clay Soil</option>
                        <option>Loamy Soil</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Current Temperature (°C)</label>
                    <input type="number" id="irr-temp" placeholder="e.g. 28">
                </div>
                <div class="form-group">
                    <label>Humidity (%)</label>
                    <input type="number" id="irr-humidity" placeholder="e.g. 65">
                </div>
                <div class="form-group">
                    <label>Last Rainfall / Irrigation (days ago)</label>
                    <input type="number" id="irr-days" placeholder="e.g. 3">
                </div>
                <div class="form-group">
                    <label>Language</label>
                    <select id="irr-lang">
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="kn">Kannada</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="getIrrigation()"><i class="fas fa-tint"></i> Get Irrigation Advice</button>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-info-circle"></i> Irrigation Recommendation</div>
                <div id="irr-result" class="result-box" style="min-height:200px;">Fill in the form to get smart irrigation advice.</div>
            </div>
        </div>
    </div>

    <!-- FERTILIZER -->
    <div class="section" id="sec-fertilizer">
        <div class="section-header"><i class="fas fa-flask"></i> Fertilizer Engine</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-flask"></i> Fertilizer Parameters</div>
                <div class="form-group">
                    <label>Crop Name</label>
                    <input type="text" id="fert-crop" placeholder="e.g. Rice, Tomato, Wheat">
                </div>
                <div class="form-group">
                    <label>Growth Stage</label>
                    <select id="fert-stage">
                        <option value="early">Early Stage (Sowing / Germination)</option>
                        <option value="mid">Mid Stage (Vegetative / Flowering)</option>
                        <option value="late">Late Stage (Fruiting / Pre-Harvest)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Soil Type</label>
                    <select id="fert-soil">
                        <option>Alluvial Soil</option>
                        <option>Black Cotton Soil</option>
                        <option>Red Soil</option>
                        <option>Sandy Soil</option>
                        <option>Clay Soil</option>
                        <option>Loamy Soil</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Language</label>
                    <select id="fert-lang">
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="kn">Kannada</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="getFertilizer()"><i class="fas fa-flask"></i> Get Recommendation</button>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-info-circle"></i> Fertilizer Recommendation</div>
                <div id="fert-result" class="result-box" style="min-height:200px;">Fill in the form to get fertilizer advice.</div>
            </div>
        </div>
    </div>

    <!-- MANDI PRICES -->
    <div class="section" id="sec-mandi">
        <div class="section-header"><i class="fas fa-store"></i> Karnataka Mandi Prices</div>
        <div class="card">
            <div class="card-title"><i class="fas fa-search"></i> Search Market Prices</div>
            <div style="display:grid; grid-template-columns:1fr 1fr auto; gap:10px; flex-wrap:wrap;">
                <div class="form-group" style="margin:0">
                    <label>Commodity</label>
                    <input type="text" id="mandi-crop" placeholder="e.g. Tomato, Rice, Onion">
                </div>
                <div class="form-group" style="margin:0">
                    <label>District (optional)</label>
                    <input type="text" id="mandi-district" placeholder="e.g. Bengaluru, Mysuru">
                </div>
                <div style="display:flex; align-items:flex-end;">
                    <button class="btn btn-primary" onclick="getMandiPrices()"><i class="fas fa-search"></i> Search</button>
                </div>
            </div>
            <div id="mandi-result"></div>
        </div>
    </div>

    <!-- GOVERNMENT SCHEMES -->
    <div class="section" id="sec-schemes">
        <div class="section-header"><i class="fas fa-landmark"></i> Government Schemes</div>
        <div class="card">
            <div class="scheme-tabs" id="scheme-tabs">
                <div class="scheme-tab active" onclick="filterSchemes('All')">All</div>
                <div class="scheme-tab" onclick="filterSchemes('Income Support')">Income</div>
                <div class="scheme-tab" onclick="filterSchemes('Insurance')">Insurance</div>
                <div class="scheme-tab" onclick="filterSchemes('Loan')">Loan</div>
                <div class="scheme-tab" onclick="filterSchemes('Subsidy')">Subsidy</div>
                <div class="scheme-tab" onclick="filterSchemes('Irrigation')">Irrigation</div>
                <div class="scheme-tab" onclick="filterSchemes('Soil')">Soil</div>
                <div class="scheme-tab" onclick="filterSchemes('Organic')">Organic</div>
                <div class="scheme-tab" onclick="filterSchemes('Fisheries')">Fisheries</div>
            </div>
            <div id="schemes-container"></div>
        </div>
    </div>

    <!-- CROP CALENDAR -->
    <div class="section" id="sec-calendar">
        <div class="section-header"><i class="fas fa-calendar-alt"></i> Crop Calendar</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-seedling"></i> Calendar Parameters</div>
                <div class="form-group">
                    <label>Crop Name</label>
                    <input type="text" id="cal-crop" placeholder="e.g. Rice, Wheat, Cotton">
                </div>
                <div class="form-group">
                    <label>Season</label>
                    <select id="cal-season">
                        <option>Kharif (June–October)</option>
                        <option>Rabi (November–April)</option>
                        <option>Zaid (March–June)</option>
                        <option>Year-Round</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Region / State</label>
                    <input type="text" id="cal-region" placeholder="e.g. Karnataka, Punjab">
                </div>
                <div class="form-group">
                    <label>Language</label>
                    <select id="cal-lang">
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="kn">Kannada</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="getCropCalendar()"><i class="fas fa-calendar"></i> Generate Calendar</button>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-calendar-check"></i> Crop Calendar</div>
                <div id="cal-result" class="result-box" style="min-height:200px;">Generate a crop calendar to see the schedule.</div>
            </div>
        </div>
    </div>

    <!-- YIELD ESTIMATOR -->
    <div class="section" id="sec-yield">
        <div class="section-header"><i class="fas fa-calculator"></i> Yield Estimator</div>
        <div class="card" style="max-width:600px">
            <div class="card-title"><i class="fas fa-tractor"></i> Enter Yield Details</div>
            <div class="three-col">
                <div class="form-group">
                    <label>Land Area (Acres)</label>
                    <input type="number" id="yield-area" placeholder="e.g. 5" min="0" step="0.1">
                </div>
                <div class="form-group">
                    <label>Yield per Acre (Quintals)</label>
                    <input type="number" id="yield-per-acre" placeholder="e.g. 20" min="0" step="0.1">
                </div>
                <div class="form-group">
                    <label>Market Price (₹/Quintal)</label>
                    <input type="number" id="yield-price" placeholder="e.g. 2000" min="0">
                </div>
            </div>
            <button class="btn btn-primary" onclick="calcYield()"><i class="fas fa-calculator"></i> Calculate</button>
            <div id="yield-result" style="margin-top:16px; display:none;">
                <div class="calc-result">
                    <div class="calc-result-item">
                        <div class="r-val neutral" id="y-production">-</div>
                        <div class="r-label">Total Production (Quintals)</div>
                    </div>
                    <div class="calc-result-item">
                        <div class="r-val profit" id="y-income">-</div>
                        <div class="r-label">Total Income (₹)</div>
                    </div>
                    <div class="calc-result-item">
                        <div class="r-val neutral" id="y-per-acre">-</div>
                        <div class="r-label">Income per Acre (₹)</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- EXPENSE & PROFIT -->
    <div class="section" id="sec-expense">
        <div class="section-header"><i class="fas fa-chart-pie"></i> Expense & Profit Calculator</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-minus-circle"></i> Expenses (₹)</div>
                <div class="form-group">
                    <label>Seed Cost</label>
                    <input type="number" id="exp-seed" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Fertilizer Cost</label>
                    <input type="number" id="exp-fert" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Pesticide Cost</label>
                    <input type="number" id="exp-pest" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Labour Cost</label>
                    <input type="number" id="exp-labour" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Transport Cost</label>
                    <input type="number" id="exp-transport" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Other Costs</label>
                    <input type="number" id="exp-other" placeholder="0" min="0">
                </div>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-plus-circle"></i> Income & Summary</div>
                <div class="form-group">
                    <label>Total Crop Income (₹)</label>
                    <input type="number" id="exp-income" placeholder="0" min="0">
                </div>
                <div class="form-group">
                    <label>Other Income (Subsidies, etc.)</label>
                    <input type="number" id="exp-other-income" placeholder="0" min="0">
                </div>
                <button class="btn btn-primary" onclick="calcExpense()"><i class="fas fa-calculator"></i> Calculate P&L</button>
                <div id="expense-result" style="margin-top:16px; display:none;">
                    <div class="calc-result" style="grid-template-columns:1fr 1fr;">
                        <div class="calc-result-item">
                            <div class="r-val loss" id="exp-total">-</div>
                            <div class="r-label">Total Investment (₹)</div>
                        </div>
                        <div class="calc-result-item">
                            <div class="r-val profit" id="exp-profit">-</div>
                            <div class="r-label">Net Profit / Loss (₹)</div>
                        </div>
                    </div>
                    <div id="exp-status" style="margin-top:12px; text-align:center; font-size:1.1rem; font-weight:600;"></div>
                    <div id="exp-bar-container" style="margin-top:14px;">
                        <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:var(--text-muted);">
                            <span>Expense Breakdown</span>
                        </div>
                        <div id="exp-breakdown" style="margin-top:8px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- SOIL HEALTH -->
    <div class="section" id="sec-soil">
        <div class="section-header"><i class="fas fa-seedling"></i> Soil Health Guide</div>
        <div class="two-col">
            <div class="card">
                <div class="card-title"><i class="fas fa-layer-group"></i> Select Soil Type</div>
                <div class="form-group">
                    <label>Soil Type</label>
                    <select id="soil-type" onchange="getSoilInfo()">
                        <option value="">-- Select Soil Type --</option>
                        <option>Alluvial Soil</option>
                        <option>Black Cotton Soil</option>
                        <option>Red Soil</option>
                        <option>Laterite Soil</option>
                        <option>Sandy Soil</option>
                        <option>Clay Soil</option>
                        <option>Loamy Soil</option>
                    </select>
                </div>
                <div style="margin-top:10px; font-size:0.82rem; color:var(--text-muted); line-height:1.6;">
                    <p>Select your soil type to get detailed information about:</p>
                    <ul style="margin-top:6px; padding-left:16px;">
                        <li>Suitable crops for cultivation</li>
                        <li>Fertilizer recommendations</li>
                        <li>Organic improvement methods</li>
                    </ul>
                </div>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-info-circle"></i> Soil Information</div>
                <div id="soil-result">
                    <p style="color:var(--text-muted);">Select a soil type to see detailed recommendations.</p>
                </div>
            </div>
        </div>
    </div>

</main>

<button class="fab" onclick="showSection('chat')" title="Open AI Chat"><i class="fas fa-robot"></i></button>

<script>
// ============================================================
// STATE
// ============================================================
let chatHistory = [];
let ttsEnabled = false;
let recognition = null;
let schemes = {{ schemes_json|safe }};

// ============================================================
// NAVIGATION
// ============================================================
function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('sec-' + id).classList.add('active');
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('onclick') && item.getAttribute('onclick').includes("'" + id + "'")) {
            item.classList.add('active');
        }
    });
    closeSidebar();
    if (id === 'schemes') renderSchemes('All');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('overlay').classList.toggle('show');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('show');
}

// ============================================================
// API HELPER
// ============================================================
async function apiCall(endpoint, data) {
    const res = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    return await res.json();
}

function setLoading(el, msg = 'Processing...') {
    el.innerHTML = '<span class="spinner"></span> ' + msg;
    el.className = 'result-box loading';
}

// ============================================================
// CHAT
// ============================================================
async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    appendMsg(msg, 'user');

    const typing = appendMsg('Thinking... 🌾', 'ai');

    try {
        const lang = document.getElementById('chat-lang').value;
        chatHistory.push({role: 'user', content: msg});
        const data = await apiCall('/api/chat', {message: msg, history: chatHistory, language: lang});
        typing.remove(); // Remove "Thinking..." message
        if (data.error) {
            appendMsg('❌ ' + data.error, 'ai');
        } else {
            appendMsg(data.reply, 'ai');
            chatHistory.push({role: 'assistant', content: data.reply});
            if (chatHistory.length > 12) chatHistory = chatHistory.slice(-12);
            if (ttsEnabled) speak(data.reply);
        }
    } catch(e) {
        typing.textContent = '❌ Connection error. Please try again.';
    }
}

function appendMsg(text, type) {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + type;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
}

function clearChat() {
    chatHistory = [];
    const msgs = document.getElementById('chat-messages');
    msgs.innerHTML = '<div class="msg ai">🌾 Chat cleared. How can I help you?</div>';
}

function ttsToggle() {
    ttsEnabled = !ttsEnabled;
    document.querySelector('[onclick="ttsToggle()"]').innerHTML =
        ttsEnabled ? '<i class="fas fa-volume-up"></i> TTS ON' : '<i class="fas fa-volume-mute"></i> TTS OFF';
}

function speak(text) {
    if (!window.speechSynthesis) return;
    const utt = new SpeechSynthesisUtterance(text);
    const lang = document.getElementById('chat-lang').value;
    utt.lang = lang === 'hi' ? 'hi-IN' : lang === 'kn' ? 'kn-IN' : 'en-US';
    window.speechSynthesis.speak(utt);
}

function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('voice-status').textContent = 'Voice not supported in this browser.';
        return;
    }
    if (recognition) recognition.stop();
    recognition = new SpeechRecognition();
    const lang = document.getElementById('chat-lang').value;
    recognition.lang = lang === 'hi' ? 'hi-IN' : lang === 'kn' ? 'kn-IN' : 'en-US';
    recognition.interimResults = false;
    recognition.onstart = () => document.getElementById('voice-status').textContent = '🎤 Listening...';
    recognition.onresult = (e) => {
        document.getElementById('chat-input').value = e.results[0][0].transcript;
        document.getElementById('voice-status').textContent = '✓ Got it!';
        setTimeout(() => document.getElementById('voice-status').textContent = '', 2000);
    };
    recognition.onerror = () => document.getElementById('voice-status').textContent = '❌ Voice error.';
    recognition.onend = () => {
        if (document.getElementById('voice-status').textContent === '🎤 Listening...')
            document.getElementById('voice-status').textContent = '';
    };
    recognition.start();
}

// ============================================================
// DISEASE DETECTION
// ============================================================
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            const img = document.getElementById('disease-preview');
            img.src = e.target.result;
            img.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
        document.getElementById('disease-file').files = e.dataTransfer.files;
        previewImage({files: [file]});
    }
}

function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.add('drag-over');
}

function handleDragLeave() {
    document.getElementById('upload-area').classList.remove('drag-over');
}

async function detectDisease() {
    const fileInput = document.getElementById('disease-file');
    if (!fileInput.files[0]) {
        alert('Please select a plant image first.');
        return;
    }
    const resultDiv = document.getElementById('disease-result');
    setLoading(resultDiv, 'Analyzing plant disease...');

    const reader = new FileReader();
    reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1];
        const lang = document.getElementById('disease-lang').value;
        try {
            const data = await apiCall('/api/disease', {image_base64: base64, language: lang});
            if (data.error) {
                resultDiv.className = 'result-box error';
                resultDiv.textContent = '❌ ' + data.error;
            } else {
                resultDiv.className = 'result-box';
                resultDiv.innerHTML = formatDiseaseResult(data);
            }
        } catch(e) {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = '❌ Connection error.';
        }
    };
    reader.readAsDataURL(fileInput.files[0]);
}

function formatDiseaseResult(data) {
    let html = '';
    if (data.disease) {
        html += `<div style="margin-bottom:12px;">
            <div style="font-size:0.8rem;color:var(--text-muted)">Detected Disease</div>
            <div style="font-size:1.2rem;font-weight:700;color:#ef9a9a;">${data.disease}</div>
        </div>`;
    }
    if (data.confidence) {
        const pct = Math.round(parseFloat(data.confidence) * 100);
        html += `<div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:var(--text-muted);">
                <span>Confidence</span><span>${pct}%</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
        </div>`;
    }
    if (data.treatment) {
        html += `<div>
            <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;">Treatment Advice</div>
            <div style="font-size:0.88rem;line-height:1.7;color:var(--text-light);">${data.treatment}</div>
        </div>`;
    }
    return html || data.message || 'No disease detected.';
}

// ============================================================
// WEATHER
// ============================================================
async function getWeather(lat, lon) {
    const resultDiv = document.getElementById('weather-result');
    resultDiv.innerHTML = '<div class="result-box loading"><span class="spinner"></span> Fetching weather data...</div>';

    let payload = {};
    if (lat && lon) {
        payload = {lat, lon};
    } else {
        const city = document.getElementById('weather-city').value.trim();
        if (!city) { alert('Please enter a city name.'); resultDiv.innerHTML = ''; return; }
        payload = {city};
    }

    try {
        const data = await apiCall('/api/weather', payload);
        if (data.error) {
            resultDiv.innerHTML = `<div class="result-box error">❌ ${data.error}</div>`;
        } else {
            resultDiv.innerHTML = formatWeather(data);
        }
    } catch(e) {
        resultDiv.innerHTML = '<div class="result-box error">❌ Connection error.</div>';
    }
}

function getWeatherGPS() {
    if (!navigator.geolocation) { alert('Geolocation not supported.'); return; }
    navigator.geolocation.getCurrentPosition(
        pos => getWeather(pos.coords.latitude, pos.coords.longitude),
        () => alert('Could not get location. Please enter city manually.')
    );
}

function formatWeather(d) {
    const sprayWarn = d.humidity > 80 || d.wind_speed > 20;
    const irrigate = d.humidity < 40 || d.temp > 35;
    return `
    <div class="weather-grid">
        <div class="weather-card">
            <div class="icon">${getWeatherIcon(d.condition)}</div>
            <div class="value">${d.temp}°C</div>
            <div class="label">Temperature</div>
        </div>
        <div class="weather-card">
            <div class="icon">💧</div>
            <div class="value">${d.humidity}%</div>
            <div class="label">Humidity</div>
        </div>
        <div class="weather-card">
            <div class="icon">💨</div>
            <div class="value">${d.wind_speed} m/s</div>
            <div class="label">Wind Speed</div>
        </div>
        <div class="weather-card">
            <div class="icon">🌦️</div>
            <div class="value" style="font-size:1rem;">${d.condition}</div>
            <div class="label">${d.city}</div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;">
        <div class="card" style="margin:0;padding:14px;">
            <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;">🌿 Spray Advisory</div>
            <div class="badge ${sprayWarn ? 'badge-red' : 'badge-green'}">${sprayWarn ? '⚠️ Avoid Spraying Today' : '✅ Good for Spraying'}</div>
            <p style="font-size:0.8rem;color:var(--text-muted);margin-top:8px;">${sprayWarn ? 'High humidity or wind may reduce effectiveness and cause drift.' : 'Conditions are favorable for pesticide/fertilizer spraying.'}</p>
        </div>
        <div class="card" style="margin:0;padding:14px;">
            <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;">💧 Irrigation Advisory</div>
            <div class="badge ${irrigate ? 'badge-yellow' : 'badge-green'}">${irrigate ? '⚠️ Irrigate Soon' : '✅ Irrigation Not Urgent'}</div>
            <p style="font-size:0.8rem;color:var(--text-muted);margin-top:8px;">${irrigate ? 'Low humidity or high temperature – crops may need water soon.' : 'Current conditions suggest adequate moisture for most crops.'}</p>
        </div>
    </div>`;
}

function getWeatherIcon(condition) {
    const c = (condition || '').toLowerCase();
    if (c.includes('rain')) return '🌧️';
    if (c.includes('cloud')) return '☁️';
    if (c.includes('sun') || c.includes('clear')) return '☀️';
    if (c.includes('storm') || c.includes('thunder')) return '⛈️';
    if (c.includes('snow')) return '❄️';
    if (c.includes('mist') || c.includes('fog')) return '🌫️';
    return '🌤️';
}

// ============================================================
// IRRIGATION
// ============================================================
async function getIrrigation() {
    const resultDiv = document.getElementById('irr-result');
    const crop = document.getElementById('irr-crop').value.trim();
    if (!crop) { alert('Please enter a crop name.'); return; }
    setLoading(resultDiv, 'Generating irrigation advice...');
    try {
        const data = await apiCall('/api/irrigation', {
            crop, stage: document.getElementById('irr-stage').value,
            soil: document.getElementById('irr-soil').value,
            temp: document.getElementById('irr-temp').value,
            humidity: document.getElementById('irr-humidity').value,
            days_since_rain: document.getElementById('irr-days').value,
            language: document.getElementById('irr-lang').value
        });
        resultDiv.className = 'result-box';
        resultDiv.textContent = data.error ? '❌ ' + data.error : data.advice;
        if (data.error) resultDiv.className = 'result-box error';
    } catch(e) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = '❌ Connection error.';
    }
}

// ============================================================
// FERTILIZER
// ============================================================
async function getFertilizer() {
    const resultDiv = document.getElementById('fert-result');
    const crop = document.getElementById('fert-crop').value.trim();
    if (!crop) { alert('Please enter a crop name.'); return; }
    setLoading(resultDiv, 'Generating fertilizer recommendation...');
    try {
        const data = await apiCall('/api/fertilizer', {
            crop, stage: document.getElementById('fert-stage').value,
            soil: document.getElementById('fert-soil').value,
            language: document.getElementById('fert-lang').value
        });
        resultDiv.className = 'result-box';
        resultDiv.textContent = data.error ? '❌ ' + data.error : data.recommendation;
        if (data.error) resultDiv.className = 'result-box error';
    } catch(e) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = '❌ Connection error.';
    }
}

// ============================================================
// MANDI PRICES
// ============================================================
async function getMandiPrices() {
    const resultDiv = document.getElementById('mandi-result');
    const crop = document.getElementById('mandi-crop').value.trim();
    if (!crop) { alert('Please enter a commodity name.'); return; }
    resultDiv.innerHTML = '<div class="result-box loading"><span class="spinner"></span> Fetching market prices...</div>';
    try {
        const data = await apiCall('/api/mandi', {
            crop, district: document.getElementById('mandi-district').value.trim()
        });
        if (data.error) {
            resultDiv.innerHTML = `<div class="result-box error">❌ ${data.error}</div>`;
        } else if (data.records && data.records.length > 0) {
            resultDiv.innerHTML = `<div class="mandi-grid">${data.records.map(formatMandiCard).join('')}</div>`;
        } else {
            resultDiv.innerHTML = '<div class="result-box">No price data found for your search. Try different commodity or district name.</div>';
        }
    } catch(e) {
        resultDiv.innerHTML = '<div class="result-box error">❌ Connection error.</div>';
    }
}

function formatMandiCard(r) {
    return `<div class="mandi-card">
        <div class="mandi-name">${r.commodity || r.Commodity || 'Unknown'}</div>
        <div class="mandi-price">₹${r.modal_price || r['Modal Price (Rs./Quintal)'] || r.modal_price || '-'}/Qtl</div>
        <div class="mandi-meta">
            <div>📍 ${r.market || r.Market || '-'}, ${r.district || r.District || '-'}</div>
            <div>Min: ₹${r.min_price || r['Min Price (Rs./Quintal)'] || '-'} &nbsp; Max: ₹${r.max_price || r['Max Price (Rs./Quintal)'] || '-'}</div>
            <div>📅 ${r.arrival_date || r['Arrival Date'] || '-'}</div>
        </div>
    </div>`;
}

// ============================================================
// SCHEMES
// ============================================================
function renderSchemes(filter) {
    const container = document.getElementById('schemes-container');
    const filtered = filter === 'All' ? schemes : schemes.filter(s => s.category === filter);
    container.innerHTML = filtered.map(s => `
        <div class="scheme-card">
            <span class="scheme-category">${s.category}</span>
            <div class="scheme-name">${s.name}</div>
            <div class="scheme-desc">${s.description}</div>
            <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;"><b>Eligibility:</b> ${s.eligibility}</div>
            <div class="scheme-links">
                <a href="${s.apply_link}" target="_blank" class="link-apply"><i class="fas fa-external-link-alt"></i> Apply Online</a>
                <a href="tel:${s.helpline}" class="link-helpline"><i class="fas fa-phone"></i> ${s.helpline}</a>
            </div>
        </div>
    `).join('');
}

function filterSchemes(cat) {
    document.querySelectorAll('.scheme-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderSchemes(cat);
}

// ============================================================
// CROP CALENDAR
// ============================================================
async function getCropCalendar() {
    const resultDiv = document.getElementById('cal-result');
    const crop = document.getElementById('cal-crop').value.trim();
    if (!crop) { alert('Please enter a crop name.'); return; }
    setLoading(resultDiv, 'Generating crop calendar...');
    try {
        const data = await apiCall('/api/calendar', {
            crop, season: document.getElementById('cal-season').value,
            region: document.getElementById('cal-region').value,
            language: document.getElementById('cal-lang').value
        });
        resultDiv.className = 'result-box';
        resultDiv.textContent = data.error ? '❌ ' + data.error : data.calendar;
        if (data.error) resultDiv.className = 'result-box error';
    } catch(e) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = '❌ Connection error.';
    }
}

// ============================================================
// YIELD ESTIMATOR
// ============================================================
async function calcYield() {
    const area = parseFloat(document.getElementById('yield-area').value) || 0;
    const ypa = parseFloat(document.getElementById('yield-per-acre').value) || 0;
    const price = parseFloat(document.getElementById('yield-price').value) || 0;

    if (!area || !ypa || !price) { alert('Please fill all fields.'); return; }

    const resultDiv = document.getElementById('yield-result');
    try {
        const data = await apiCall('/api/yield', { area, ypa, price });
        document.getElementById('y-production').textContent = data.production.toLocaleString('en-IN', {maximumFractionDigits: 2});
        document.getElementById('y-income').textContent = '₹' + data.income.toLocaleString('en-IN', {maximumFractionDigits: 0});
        document.getElementById('y-per-acre').textContent = '₹' + data.per_acre.toLocaleString('en-IN', {maximumFractionDigits: 0});
        resultDiv.style.display = 'block';
    } catch(e) {
        alert('Error calculating yield. Please try again.');
    }
}

// ============================================================
// EXPENSE & PROFIT CALCULATOR
// ============================================================
async function calcExpense() {
    const getVal = id => parseFloat(document.getElementById(id).value) || 0;
    const payload = {
        seed: getVal('exp-seed'),
        fert: getVal('exp-fert'),
        pest: getVal('exp-pest'),
        labour: getVal('exp-labour'),
        transport: getVal('exp-transport'),
        other: getVal('exp-other'),
        income: getVal('exp-income'),
        other_income: getVal('exp-other-income')
    };

    try {
        const data = await apiCall('/api/expense', payload);
        const totalExp = data.total_exp;
        const profit = data.profit;

        document.getElementById('exp-total').textContent = '₹' + totalExp.toLocaleString('en-IN');
        const profitEl = document.getElementById('exp-profit');
        profitEl.textContent = (profit >= 0 ? '₹' : '-₹') + Math.abs(profit).toLocaleString('en-IN');
        profitEl.className = 'r-val ' + (profit >= 0 ? 'profit' : 'loss');

        const statusEl = document.getElementById('exp-status');
        if (profit > 0) statusEl.innerHTML = '<span class="badge badge-green">✅ Profit of ₹' + profit.toLocaleString('en-IN') + '</span>';
        else if (profit < 0) statusEl.innerHTML = '<span class="badge badge-red">❌ Loss of ₹' + Math.abs(profit).toLocaleString('en-IN') + '</span>';
        else statusEl.innerHTML = '<span class="badge badge-yellow">⚖️ Break Even</span>';

    const items = data.items.filter(i => i.val > 0);
    if (totalExp > 0 && items.length > 0) {
        document.getElementById('exp-breakdown').innerHTML = items.map(i => {
            const percentage = Math.round(i.val/totalExp*100);
            return `
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:var(--text-muted);">
                        <span>${i.label}</span><span>₹${i.val.toLocaleString('en-IN')} (${percentage}%)</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill" style="width:${percentage}%"></div></div>
                </div>`;
        }).join('');
    }
    document.getElementById('expense-result').style.display = 'block';
} catch(e) {
    alert('Error calculating expenses. Please try again.');
}
}

// ============================================================
// SOIL HEALTH
// ============================================================
const soilData = {{ soil_json|safe }};

function getSoilInfo() {
    const soil = document.getElementById('soil-type').value;
    const resultDiv = document.getElementById('soil-result');
    if (!soil) { resultDiv.innerHTML = '<p style="color:var(--text-muted);">Select a soil type to see recommendations.</p>'; return; }
    const data = soilData[soil];
    if (!data) { resultDiv.innerHTML = '<p style="color:var(--text-muted);">No data found.</p>'; return; }

    resultDiv.innerHTML = `
        <div class="soil-info-item">
            <h4>🌾 Suitable Crops</h4>
            <div class="crop-tags">${data.suitable_crops.map(c => `<span class="crop-tag">${c}</span>`).join('')}</div>
        </div>
        <div class="soil-info-item">
            <h4>🧪 Fertilizer Recommendation</h4>
            <p>${data.fertilizer}</p>
        </div>
        <div class="soil-info-item">
            <h4>🌿 Organic Improvement</h4>
            <p>${data.organic_improvement}</p>
        </div>`;
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    renderSchemes('All');
});
</script>
</body>
</html>
"""


def call_groq(messages, max_tokens=1024):
    if not GROQ_API_KEY:
        return None, "GROQ_API_KEY is not configured. Please add it to environment secrets."
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": max_tokens},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except Exception as e:
        return None, f"AI service error: {str(e)}"


LANG_MAP = {"en": "English", "hi": "Hindi", "kn": "Kannada"}


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        schemes_json=json.dumps(GOVERNMENT_SCHEMES),
        soil_json=json.dumps(SOIL_DATA)
    )


@app.route("/api/yield", methods=["POST"])
def calculate_yield():
    data = request.json
    area = float(data.get("area", 0))
    ypa = float(data.get("ypa", 0))
    price = float(data.get("price", 0))
    production = area * ypa
    income = production * price
    per_acre = income / area if area > 0 else 0
    return jsonify({
        "production": production,
        "income": income,
        "per_acre": per_acre
    })


@app.route("/api/expense", methods=["POST"])
def calculate_expense():
    data = request.json
    seed = float(data.get("seed", 0))
    fert = float(data.get("fert", 0))
    pest = float(data.get("pest", 0))
    labour = float(data.get("labour", 0))
    transport = float(data.get("transport", 0))
    other = float(data.get("other", 0))
    income = float(data.get("income", 0))
    other_income = float(data.get("other_income", 0))

    total_exp = seed + fert + pest + labour + transport + other
    total_income = income + other_income
    profit = total_income - total_exp

    return jsonify({
        "total_exp": total_exp,
        "profit": profit,
        "items": [
            {"label": "Seed", "val": seed},
            {"label": "Fertilizer", "val": fert},
            {"label": "Pesticide", "val": pest},
            {"label": "Labour", "val": labour},
            {"label": "Transport", "val": transport},
            {"label": "Other", "val": other}
        ]
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    history = data.get("history", [])[-10:]
    lang = data.get("language", "en")
    lang_name = LANG_MAP.get(lang, "English")

    system_prompt = f"""You are Bharat Farming Assistant AI, an expert agricultural advisor for Indian farmers.
    You help with crops, diseases, weather, irrigation, fertilizers, government schemes, and market prices.
    Always respond in {lang_name}. Keep responses concise, practical, and farmer-friendly.
    Focus on Indian farming context, crops, and conditions."""

    messages = [{"role": "system", "content": system_prompt}] + history[-10:] + [{"role": "user", "content": message}]
    reply, error = call_groq(messages, max_tokens=600)
    if error:
        return jsonify({"error": error})
    return jsonify({"reply": reply})


@app.route("/api/disease", methods=["POST"])
def disease():
    data = request.json
    image_b64 = data.get("image_base64", "")
    lang = data.get("language", "en")
    lang_name = LANG_MAP.get(lang, "English")

    if not image_b64:
        return jsonify({"error": "No image provided."})

    plant_id_key = PLANT_ID_API_KEY
    if not plant_id_key:
        return jsonify({"error": "PLANT_ID_API_KEY not configured. Please add it to environment secrets."})

    try:
        resp = requests.post(
            "https://api.plant.id/v2/health_assessment",
            headers={"Api-Key": plant_id_key, "Content-Type": "application/json"},
            json={"images": [image_b64], "modifiers": ["crops_fast", "similar_images"], "plant_language": "en",
                  "health": "all"},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        diseases = result.get("health_assessment", {}).get("diseases", [])
        if not diseases:
            return jsonify({"message": "No disease detected. The plant appears healthy!", "disease": "Healthy",
                            "confidence": "1.0",
                            "treatment": "No treatment needed. Maintain good agricultural practices."})

        top = diseases[0]
        disease_name = top.get("name", "Unknown")
        confidence = top.get("probability", 0)

        prompt = f"""A crop disease has been detected: {disease_name} (confidence: {round(confidence * 100)}%).
    Provide treatment advice for Indian farmers in {lang_name}:
    1. Immediate action to take
    2. Fungicide/pesticide recommendations (include brand names available in India)
    3. Organic/natural treatment options
    4. Prevention for next season
    Keep it practical and brief."""

        treatment, err = call_groq([{"role": "user", "content": prompt}], max_tokens=500)
        if err:
            treatment = f"Please consult your local agricultural officer for treatment of {disease_name}."

        return jsonify({"disease": disease_name, "confidence": str(confidence), "treatment": treatment})
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Plant.id API error: {e.response.status_code}. Check your API key."})
    except Exception as e:
        return jsonify({"error": f"Disease detection error: {str(e)}"})


@app.route("/api/weather", methods=["POST"])
def weather():
    data = request.json
    if not OPENWEATHER_API_KEY:
        return jsonify({"error": "OPENWEATHER_API_KEY not configured. Please add it to environment secrets."})

    try:
        params = {"appid": OPENWEATHER_API_KEY, "units": "metric"}
        if "city" in data:
            params["q"] = data["city"]
        elif "lat" in data:
            params["lat"] = data["lat"]
            params["lon"] = data["lon"]
        else:
            return jsonify({"error": "City or coordinates required."})

        resp = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=15)
        resp.raise_for_status()
        w = resp.json()

        return jsonify({
            "city": w.get("name", "Unknown"),
            "temp": round(w["main"]["temp"], 1),
            "humidity": w["main"]["humidity"],
            "condition": w["weather"][0]["description"].title(),
            "wind_speed": round(w.get("wind", {}).get("speed", 0), 1),
            "feels_like": round(w["main"]["feels_like"], 1)
        })
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "City not found. Please check the spelling."})
        return jsonify({"error": f"Weather API error: {e.response.status_code}"})
    except Exception as e:
        return jsonify({"error": f"Weather error: {str(e)}"})


@app.route("/api/irrigation", methods=["POST"])
def irrigation():
    data = request.json
    lang_name = LANG_MAP.get(data.get("language", "en"), "English")

    prompt = f"""Provide smart irrigation advice for an Indian farmer in {lang_name}.

    Crop: {data.get('crop')}
    Growth Stage: {data.get('stage')}
    Soil Type: {data.get('soil')}
    Current Temperature: {data.get('temp', 'unknown')}°C
    Humidity: {data.get('humidity', 'unknown')}%
    Days Since Last Rain/Irrigation: {data.get('days_since_rain', 'unknown')} days

    Provide:
    1. Should irrigate today? (Yes/No with reason)
    2. How much water (liters per acre or cm depth)?
    3. Best time of day to irrigate
    4. Irrigation method recommendation (drip/sprinkler/flood)
    5. Next irrigation schedule

    Keep advice practical, specific, and concise."""

    advice, error = call_groq([{"role": "user", "content": prompt}], max_tokens=400)
    if error:
        return jsonify({"error": error})
    return jsonify({"advice": advice})


@app.route("/api/fertilizer", methods=["POST"])
def fertilizer():
    data = request.json
    lang_name = LANG_MAP.get(data.get("language", "en"), "English")

    prompt = f"""Provide fertilizer recommendations for an Indian farmer in {lang_name}.

    Crop: {data.get('crop')}
    Growth Stage: {data.get('stage')}
    Soil Type: {data.get('soil')}

    Provide:
    1. Chemical fertilizers needed (NPK ratios, doses per acre, timing)
    2. Specific fertilizer names available in India (Urea, DAP, MOP, etc.)
    3. Organic alternative tip (compost, vermicompost, green manure)
    4. Application method (broadcast/drip/foliar spray)
    5. Important warnings or deficiency signs to watch for

    Keep it practical and farmer-friendly."""

    rec, error = call_groq([{"role": "user", "content": prompt}], max_tokens=500)
    if error:
        return jsonify({"error": error})
    return jsonify({"recommendation": rec})


@app.route("/api/mandi", methods=["POST"])
def mandi():
    data = request.json
    crop = data.get("crop", "").strip()
    district = data.get("district", "").strip()

    if not crop:
        return jsonify({"error": "Commodity name is required."})

    api_key = DATA_GOV_API_KEY
    if not api_key:
        return jsonify({"error": "DATA_GOV_API_KEY not configured. Please add it to environment secrets."})

    try:
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": "50",
            "filters[state.keyword]": "Karnataka",
            "filters[commodity]": crop
        }
        if district:
            params["filters[district]"] = district

        resp = requests.get(
            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
            params=params,
            timeout=20
        )
        resp.raise_for_status()
        result = resp.json()
        records = result.get("records", [])
        return jsonify({"records": records, "total": result.get("total", 0)})
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Data.gov API error: {e.response.status_code}. Check your API key."})
    except Exception as e:
        return jsonify({"error": f"Mandi price error: {str(e)}"})


@app.route("/api/calendar", methods=["POST"])
def calendar():
    data = request.json
    lang_name = LANG_MAP.get(data.get("language", "en"), "English")

    prompt = f"""Create a detailed crop calendar for an Indian farmer in {lang_name}.

    Crop: {data.get('crop')}
    Season: {data.get('season')}
    Region: {data.get('region', 'India')}

    Provide a month-by-month schedule covering:
    1. Land Preparation & Sowing (dates, seed rate, spacing)
    2. Fertilizer Schedule (what, when, how much per acre)
    3. Irrigation Schedule (frequency and amount)
    4. Pest & Disease Management (key monitoring periods)
    5. Harvesting (expected time, method, yield)

    Format as a clear, practical timeline."""

    cal, error = call_groq([{"role": "user", "content": prompt}], max_tokens=700)
    if error:
        return jsonify({"error": error})
    return jsonify({"calendar": cal})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
