"""Explainable offline ingredient-aware recipe retrieval (not generative AI)."""
import json
import re
from pathlib import Path
from difflib import get_close_matches
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_FILE = Path(__file__).with_name('recipes.json')
ALIASES = {
 'eggs':'egg','tomatoes':'tomato','cherry tomatoes':'tomato','potatoes':'potato',
 'mushrooms':'mushroom','carrots':'carrot','onions':'onion',
 'bell peppers':'bell pepper','peppers':'bell pepper','capsicum':'bell pepper',
 'chickpeas':'chickpea','garbanzo beans':'chickpea','lentils':'lentil',
 'black beans':'black bean','kidney beans':'black bean','green peas':'peas','frozen peas':'peas',
 'oatmeal':'oats','rolled oats':'oats','mozzarella cheese':'mozzarella',
 'parmesan cheese':'parmesan','feta cheese':'feta','cheddar cheese':'cheese',
 'cheddar':'cheese','grated cheese':'cheese','shredded cheese':'cheese','sliced cheese':'cheese',
 'spaghetti':'pasta','macaroni':'pasta','penne':'pasta','fusilli':'pasta',
 'rice noodles':'rice noodles','chicken breast':'chicken','chicken thighs':'chicken',
 'tinned tuna':'tuna','canned tuna':'tuna','canned tomatoes':'tomato',
 'tinned tomatoes':'tomato','canned chickpeas':'chickpea',
 'garlic cloves':'garlic','cloves of garlic':'garlic','courgette':'zucchini',
 'courgettes':'zucchini','whole milk':'milk','spring onions':'spring onion',
 'tortillas':'tortilla','bananas':'banana','cucumbers':'cucumber','avocados':'avocado',
 'lemons':'lemon','limes':'lime','olives':'olive','chicken broth':'chicken stock',
 'vegetable broth':'vegetable stock','spinach leaves':'spinach',
 'olive oil':'olive oil','vegetable oil':'oil','sunflower oil':'oil',
 'coconut cream':'coconut milk', 'aubergine':'eggplant', 'aubergines':'eggplant',
 'garlic powder':'garlic powder', 'soy milk':'soy milk','oat milk':'oat milk',
 'almond milk':'almond milk', 'tomato sauce':'tomato sauce',
}
# Deliberate, transparent substitutes; avoid conflating allergen groups or raw ingredients with sauces.
SUBSTITUTES = {
 'pasta': {'spaghetti','penne','macaroni','fusilli'},
 'olive oil': {'oil'},
 'oil': {'olive oil'},
 'cheese': {'mozzarella','parmesan'},
 'milk': set(),
 'butter': set(),
 'red onion': {'onion'}, 'onion': {'red onion'},
 'bread': {'toast'}, 'noodles': {'rice noodles'},
}
PANTRY = {'salt','pepper','oil','olive oil','water'}

def clean(token):
    token = re.sub(r'\s+', ' ', token.lower().strip())
    token = re.sub(r'[^a-z\- ]', '', token)
    return ALIASES.get(token, token)

def parse_ingredients(text):
    return list(dict.fromkeys(x for item in re.split(r'[,;\n]+',text) if (x:=clean(item))))

def load_recipes():
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))

def _match(required, available):
    if required in available:
        return required, False
    for alternative in sorted(SUBSTITUTES.get(required, [])):
        if alternative in available:
            return alternative, True
    return None, False

def recommend(text, diet='Any', max_missing=5, max_minutes=60, limit=12,
              pantry_staples=False, only_ready=False, exclude='', priority='Closest match'):
    available = set(parse_ingredients(text))
    if not available:
        return []
    effective = available | (PANTRY if pantry_staples else set())
    forbidden = set(parse_ingredients(exclude))
    if available & forbidden:
        available -= forbidden
        effective -= forbidden
    recipes = [r for r in load_recipes() if r['minutes'] <= max_minutes
               and (diet == 'Any' or diet.lower() in r['tags'])
               and not any(_match(item, forbidden)[0] is not None for item in r['ingredients'])]
    if not recipes:
        return []
    # Use TF-IDF only as a secondary tie-breaker. Exact ingredient coverage governs rankings.
    corpus = [' | '.join(sorted(set(r['ingredients']))) for r in recipes]
    vectorizer = TfidfVectorizer(tokenizer=lambda s: s.split(' | '), token_pattern=None,
                                 lowercase=False)
    matrix = vectorizer.fit_transform(corpus + [' | '.join(sorted(effective))])
    sims = cosine_similarity(matrix[-1],matrix[:-1]).ravel()
    output=[]
    for r,sim in zip(recipes,sims):
        matched=[];missing=[];substituted=[];pantry_used=[]
        for required in r['ingredients']:
            actual, used_sub = _match(required,effective)
            if actual is None:
                missing.append(required)
            else:
                matched.append(required)
                if actual not in available:
                    pantry_used.append(required)
                if used_sub:
                    substituted.append((required,actual))
        real_matches = len(matched)-len(pantry_used)
        if not real_matches or len(missing)>max_missing or (only_ready and missing):
            continue
        coverage = len(matched)/len(r['ingredients'])
        # Strictly order by fewer missing ingredients; prefer higher coverage and real matches.
        score = round(coverage,3)
        output.append({**r,'matched':matched,'missing':missing,'coverage':coverage,
                       'score':score,'similarity':float(sim),
                       'substituted':substituted,'pantry_used':pantry_used,
                       'ready':not missing,'real_matches':real_matches})
    if priority == 'Use more of my ingredients':
        output.sort(key=lambda r:(len(r['missing']) > 0, -r['real_matches'],
                                  len(r['missing']), -r['coverage'], -r['similarity'], r['minutes']))
    elif priority == 'Fastest cooking':
        output.sort(key=lambda r:(len(r['missing']) > 0,r['minutes'],len(r['missing']),-r['coverage']))
    else:
        output.sort(key=lambda r:(len(r['missing']),-r['coverage'],-r['real_matches'],
                                  -r['similarity'],r['minutes']))
    return output[:limit]
