# 🥕 FridgeChef AI

A working, offline recipe recommender for the Advanced AI Algorithms group assignment. Users enter ingredients they have in the fridge and get ranked recipes with instructions and a missing-ingredients shopping list.

## Start on Mac

Install Python 3.11 or 3.12 (recommended). In Terminal:

```bash
cd ~/Downloads/fridgechef_ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If the extracted folder lives somewhere else: type `cd ` then drag it from Finder into Terminal and press Return. The app normally appears at http://localhost:8501.

## How to use
1. Enter ingredients separated by commas (e.g. `eggs, tomato, cheese, mushroom, bread`).
2. Adjust dietary preference, max cooking time, and how many missing ingredients you're willing to buy.
3. Click **Find my recipes**.
4. Recipes rank by available ingredients; click **View cooking steps**.

## How the algorithm works

The included `recipes.json` contains a curated sample catalog of 20 recipes with ingredient lists, dietary tags, time and steps. `engine.py` normalizes common ingredient synonyms. It builds **TF-IDF ingredient vectors** and measures **cosine similarity** between the user's ingredients and each recipe; it combines similarity (25%) with exact ingredient coverage (75%). Filters enforce cooking-time and dietary-tag selections. The user can inspect matched and missing ingredients. This is a retrieval/recommendation algorithm, not generative AI; it does not invent recipes.

For a stronger AAA project, benchmark against ingredient-overlap-only ranking and evaluate with held-out user profiles. Include these metrics in your demo rather than making unmeasured accuracy claims.

## Project files
- `app.py`: Streamlit dashboard
- `engine.py`: ingredient parsing + ranking algorithm
- `recipes.json`: original, manually authored sample data
- `requirements.txt`: dependencies
- `test_engine.py`: reproducible unit tests
- `AI_USE_LOG.md`: prompt transparency template

## Limitations
- A small illustrative recipe catalog, not live or exhaustive.
- Dietary labels are approximate; recipe entries may contain allergens or ingredients unsuitable for individual needs. Check labels and ingredients carefully (e.g. soy sauce may contain wheat).
- Some synonyms are normalized, but free-text and quantities are not fully parsed.
- It gives meal ideas, not personal medical/nutrition advice.

## Data and citations
Recipe examples and cooking steps were written for this project, without downloading copyrighted recipe databases. Key packages: Python, Streamlit, scikit-learn, pandas. No API key, network traffic, or model download is required to run the app once dependencies are installed.

## Suggested five-minute demo
0:00–0:40 problem of food waste; 0:40–1:20 solution and relevance; 1:20–3:20 live demo with different ingredients; 3:20–4:15 ML approach, limitations and evaluation; 4:15–5:00 future expansion (larger recipe corpus, personalized nutrition filters, vision-based fridge recognition).
