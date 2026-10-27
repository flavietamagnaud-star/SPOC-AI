"""Optional local generative recipes via Ollama; no internet API key needed.

Requires Ollama running locally with a downloaded model. Never claim generation
when the local model is unavailable.
"""
import json
import urllib.request
import urllib.error
from engine import parse_ingredients, clean

OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'

class RecipeGenerationError(Exception):
    pass


def generate_recipe(ingredients, diet='Any', avoid='', minutes=30, model='llama3.2:3b', api_key=None):
    available = parse_ingredients(ingredients)
    excluded = parse_ingredients(avoid)
    if not available:
        raise RecipeGenerationError('Enter at least one ingredient first.')
    if len(available) > 40:
        raise RecipeGenerationError('Please enter no more than 40 ingredients.')
    if len(excluded) > 30:
        raise RecipeGenerationError('Please enter no more than 30 excluded ingredients.')
    diet_rule = diet if diet in {'Any','Vegetarian','Vegan','Gluten-free','Dairy-free'} else 'Any'
    system = ('You are a practical home-cooking assistant. Output exactly one valid JSON object, no markdown. '
              'Use only listed ingredients as available. Pantry items are NOT assumed available unless listed. '
              'Keep missing ingredients to a minimum, ideally zero, and indicate all required ingredients. '
              'Respect excluded foods and the dietary preference. Do not recommend unsafe food handling. '
              'Avoid claiming allergy safety. Provide clear, practical and safe cooking instructions. '
              'Output keys: name (string), description (string), minutes (integer), '
              'ingredients (array of strings), steps (array of strings), tips (string).')
    user = json.dumps({'available_ingredients':available, 'avoid':excluded,
                       'diet':diet_rule, 'maximum_minutes':int(minutes)},ensure_ascii=False)
    if api_key:
        body = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            'response_format': {'type': 'json_object'},
        }
        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + api_key},
            method='POST',
        )
    else:
        body = {'model': model, 'system': system, 'prompt': user,
                'stream': False, 'format': 'json',
                'options': {'temperature': 0.4, 'num_predict': 650}}
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
    try:
        with urllib.request.urlopen(req, timeout=100) as resp:
            response = json.load(resp)
        generated_text = response['choices'][0]['message']['content'] if api_key else response['response']
    except urllib.error.HTTPError as exc:
        if api_key:
            raise RecipeGenerationError('Cloud AI request failed (HTTP ' + str(exc.code) + '). Check that your API key is valid and your API account has available credits.') from exc
        raise RecipeGenerationError('Local Ollama request failed (HTTP ' + str(exc.code) + '). Check the model name.') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if api_key:
            raise RecipeGenerationError('Unable to connect to the cloud AI service. Please try again.') from exc
        raise RecipeGenerationError('Could not reach Ollama. Make sure Ollama is installed, running, and the model has been downloaded.') from exc
    except (KeyError, IndexError, TypeError) as exc:
        raise RecipeGenerationError('AI response was not in the expected format. Please try again.') from exc
    try:
        result = json.loads(generated_text)
        if not isinstance(result,dict): raise ValueError('Expected an object')
        name = str(result['name']).strip()
        description = str(result.get('description','')).strip()
        used = [clean(str(s)) for s in result['ingredients']]
        steps = [str(s).strip() for s in result['steps']]
        duration = int(result['minutes'])
        if not name or not used or not steps or duration < 1 or duration > 300:
            raise ValueError('Incomplete recipe')
    except (KeyError,ValueError,TypeError, json.JSONDecodeError) as exc:
        raise RecipeGenerationError('The model returned an incomplete recipe. Please try again.') from exc
    blocked = sorted(set(used)&set(excluded))
    missing = sorted(set(used)-set(available))
    warnings = []
    if blocked: warnings.append('The model included an excluded ingredient: '+', '.join(blocked)+'. Do not use this suggestion.')
    if duration > int(minutes): warnings.append('Estimated cooking time exceeds your limit.')
    if diet_rule != 'Any': warnings.append('Verify dietary suitability and allergens manually; generative models can make mistakes.')
    return {'name':name,'description':description,'minutes':duration,'ingredients':used,
            'steps':steps,'tips':str(result.get('tips','')).strip(),
            'missing':missing,'blocked':blocked,'warnings':warnings,'model':model}
