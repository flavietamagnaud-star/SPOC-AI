"""FridgeChef AI - polished Streamlit demo with offline recipe pictures."""
import streamlit as st
from engine import recommend, parse_ingredients, load_recipes
from generator import generate_recipe, RecipeGenerationError
from visuals import get_recipe_image

st.set_page_config(page_title='FridgeChef AI', page_icon='🥕', layout='wide')

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {
        background: linear-gradient(120deg, #19392f 0%, #2b8f5b 100%);
        color: white; border-radius: 24px; padding: 28px 30px; margin-bottom: 1.2rem;
        box-shadow: 0 14px 35px rgba(0,0,0,.12);
    }
    .hero h1 {margin: 0; font-size: 2.6rem; color: white;}
    .hero p {margin: .35rem 0 0 0; color: #e9f7ef; font-size: 1.05rem;}
    .soft-card {
        background: #f7faf8; border: 1px solid #e6efea; border-radius: 18px; padding: 14px 16px;
        min-height: 102px;
    }
    .mini-badge {
        display: inline-block; padding: .28rem .62rem; border-radius: 999px; font-size: .82rem;
        margin-right: .35rem; margin-bottom: .35rem; background: #eef6f1; color: #24563f;
        border: 1px solid #d9ebe0;
    }
    .section-title {margin-top: .25rem; margin-bottom: .6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

if 'fridge' not in st.session_state:
    st.session_state.fridge = 'egg, tomato, cheese, milk, butter'
if 'avoid' not in st.session_state:
    st.session_state.avoid = ''
if 'searched' not in st.session_state:
    st.session_state.searched = False
if 'saved' not in st.session_state:
    st.session_state.saved = []
if 'generated' not in st.session_state:
    st.session_state.generated = None

def choose_example(fridge_text, avoid_text=''):
    """Called before Streamlit renders the bound text input widgets."""
    st.session_state.fridge = fridge_text
    st.session_state.avoid = avoid_text
    st.session_state.searched = True
    st.session_state.generated = None


def clear_inputs():
    st.session_state.fridge = ''
    st.session_state.avoid = ''
    st.session_state.searched = False
    st.session_state.generated = None


all_recipes = load_recipes()

st.markdown(
    """
    <div class="hero">
      <h1>🥕 FridgeChef AI</h1>
      <p>Tell the app what you have in your fridge and get recipe ideas you can actually cook — plus shopping help and optional AI-generated meals.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header('⚙️ Preferences')
    diet = st.selectbox('Dietary preference', ['Any', 'Vegetarian', 'Vegan', 'Gluten-free', 'Dairy-free'])
    max_minutes = st.slider('Maximum cooking time', 10, 75, 45, 5, format='%d min')
    only_ready = st.checkbox('Show only recipes I can cook now', value=False)
    max_missing = 0 if only_ready else st.slider('Maximum missing ingredients', 0, 8, 3)
    pantry = st.checkbox('Assume I have salt, pepper, oil and water', value=False)
    priority = st.selectbox('Sort results by', ['Closest match', 'Use more of my ingredients', 'Fastest cooking'])
    st.divider()
    st.markdown('**Quick examples**')
    st.button('🍳 Breakfast', use_container_width=True, on_click=choose_example,
              args=('egg, bread, tomato, cheese, milk, butter',))
    st.button('🍝 Pasta night', use_container_width=True, on_click=choose_example,
              args=('pasta, tomato, garlic, parmesan, olive oil, basil',))
    st.button('🥗 Vegetarian', use_container_width=True, on_click=choose_example,
              args=('chickpea, tomato, cucumber, feta, red onion, olive oil', 'chicken, beef'))
    st.divider()
    st.caption('Recipe search works without an API key. AI recipe generation requires a cloud API key on this published app.')

col_a, col_b = st.columns([1.7, 1])
with col_a:
    st.subheader('🥬 What do you have in your fridge?')
    st.text_area(
        'Enter ingredients separated by commas',
        key='fridge',
        height=120,
        placeholder='For example: eggs, tomatoes, mozzarella, pasta, garlic',
        label_visibility='collapsed',
    )
    st.text_input('Ingredients to avoid (optional)', key='avoid', placeholder='For example: peanuts, mushrooms')
    btn1, btn2, btn3 = st.columns([1.2, 1, 1])
    with btn1:
        if st.button('✨ Find my recipes', type='primary', use_container_width=True):
            st.session_state.searched = True
    with btn2:
        st.button('🔄 Try example', use_container_width=True, on_click=choose_example,
                  args=('pasta, tomato, garlic, mushroom, olive oil, parmesan',))
    with btn3:
        st.button('🧹 Clear', use_container_width=True, on_click=clear_inputs)

with col_b:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('### Why this app is useful')
    st.write('• Save time deciding what to cook')
    st.write('• Reduce food waste')
    st.write('• See what extra ingredients you still need')
    st.write('• Generate a brand-new recipe if you want something original')
    st.markdown('</div>', unsafe_allow_html=True)

# Main tabs
find_tab, create_tab, saved_tab = st.tabs(['🍽️ Discover recipes', '🧠 Create a new recipe', '🛒 Saved recipes'])

with find_tab:
    ingredients = parse_ingredients(st.session_state.fridge)
    if not st.session_state.searched:
        st.info('Enter your ingredients above and click **Find my recipes** to see the best matches.')
    elif not ingredients:
        st.warning('Please enter at least one ingredient.')
    else:
        results = recommend(
            st.session_state.fridge,
            diet,
            max_missing,
            max_minutes,
            limit=24,
            pantry_staples=pantry,
            only_ready=only_ready,
            exclude=st.session_state.avoid,
            priority=priority,
        )
        ready = [r for r in results if r['ready']]
        almost = [r for r in results if not r['ready']]

        st.caption('Recognized ingredients: ' + ', '.join(ingredients))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric('Ready now', len(ready))
        m2.metric('Need extra items', len(almost))
        m3.metric('Catalog size', len(all_recipes))
        avg_minutes = round(sum(r['minutes'] for r in results[:5]) / max(1, len(results[:5]))) if results else 0
        m4.metric('Avg. top cooking time', f'{avg_minutes} min')

        if not results:
            st.warning('No recipes match these filters. Try increasing the allowed missing ingredients or choosing a less restrictive dietary preference.')
        else:
            if ready:
                st.markdown('### ✅ Recipes you can make now')
                st.caption('These recipes are the best immediate matches based on what you already have.')
                for recipe in ready:
                    img_col, info_col = st.columns([1.15, 1.85])
                    with img_col:
                        st.image(get_recipe_image(recipe), use_container_width=True)
                    with info_col:
                        st.markdown(f'### {recipe["name"]}')
                        st.write(recipe['description'])
                        badges = [
                            f'<span class="mini-badge">⏱️ {recipe["minutes"]} min</span>',
                            f'<span class="mini-badge">✅ Ready now</span>',
                            *[f'<span class="mini-badge">{tag.title()}</span>' for tag in recipe['tags'][:3]],
                        ]
                        st.markdown(' '.join(badges), unsafe_allow_html=True)
                        st.progress(recipe['coverage'], text=f"{recipe['coverage']:.0%} of ingredients available")
                        st.markdown('**You already have:** ' + ', '.join(recipe['matched']))
                        st.markdown('**You still need:** Nothing else 🎉')
                        if recipe['pantry_used']:
                            st.caption('Pantry staples assumed: ' + ', '.join(recipe['pantry_used']))
                        if recipe['substituted']:
                            st.caption('Ingredient alternatives used: ' + ', '.join(f'{need} → {actual}' for need, actual in recipe['substituted']))
                        act1, act2 = st.columns([1, 1])
                        with act1:
                            label = '⭐ Save recipe' if recipe['name'] not in st.session_state.saved else '✅ Saved'
                            if st.button(label, key=f'save_ready_{recipe["name"]}', use_container_width=True):
                                if recipe['name'] not in st.session_state.saved:
                                    st.session_state.saved.append(recipe['name'])
                                else:
                                    st.session_state.saved.remove(recipe['name'])
                                st.rerun()
                        with act2:
                            with st.expander('👩‍🍳 Show recipe steps'):
                                for i, step in enumerate(recipe['steps'], 1):
                                    st.write(f'{i}. {step}')
                                if recipe.get('optional'):
                                    st.caption('Optional additions: ' + ', '.join(recipe['optional']))
                    st.divider()

            if almost:
                st.markdown('### 🛒 Close matches')
                st.caption('These recipes are still good ideas, but you will need a few extra ingredients. Some of the expanded catalog is template-derived; check steps and ingredient quantities before cooking.')
                for recipe in almost:
                    img_col, info_col = st.columns([1.15, 1.85])
                    with img_col:
                        st.image(get_recipe_image(recipe), use_container_width=True)
                    with info_col:
                        st.markdown(f'### {recipe["name"]}')
                        st.write(recipe['description'])
                        missing_count = len(recipe['missing'])
                        badges = [
                            f'<span class="mini-badge">⏱️ {recipe["minutes"]} min</span>',
                            f'<span class="mini-badge">Missing {missing_count}</span>',
                            *[f'<span class="mini-badge">{tag.title()}</span>' for tag in recipe['tags'][:3]],
                        ]
                        st.markdown(' '.join(badges), unsafe_allow_html=True)
                        st.progress(recipe['coverage'], text=f"{recipe['coverage']:.0%} of ingredients available")
                        st.markdown('**You already have:** ' + ', '.join(recipe['matched']))
                        st.markdown('**You still need:** ' + ', '.join(recipe['missing']))
                        if recipe['pantry_used']:
                            st.caption('Pantry staples assumed: ' + ', '.join(recipe['pantry_used']))
                        if recipe['substituted']:
                            st.caption('Ingredient alternatives used: ' + ', '.join(f'{need} → {actual}' for need, actual in recipe['substituted']))
                        act1, act2 = st.columns([1, 1])
                        with act1:
                            label = '⭐ Save recipe' if recipe['name'] not in st.session_state.saved else '✅ Saved'
                            if st.button(label, key=f'save_almost_{recipe["name"]}', use_container_width=True):
                                if recipe['name'] not in st.session_state.saved:
                                    st.session_state.saved.append(recipe['name'])
                                else:
                                    st.session_state.saved.remove(recipe['name'])
                                st.rerun()
                        with act2:
                            with st.expander('👩‍🍳 Show recipe steps'):
                                for i, step in enumerate(recipe['steps'], 1):
                                    st.write(f'{i}. {step}')
                                if recipe.get('optional'):
                                    st.caption('Optional additions: ' + ', '.join(recipe['optional']))
                    st.divider()

with create_tab:
    st.subheader('🧠 Optional generative AI — credentials required')
    st.info('The main recipe finder works without payment or API credentials. Creating entirely new recipes requires a separately configured online AI provider and a valid API key. This is an optional experimental feature, not required to use FridgeChef.')
    import os
    try:
        api_key = st.secrets.get('OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
    except (FileNotFoundError, KeyError):
        api_key = os.environ.get('OPENAI_API_KEY', '')
    api_key = str(api_key).strip()
    if api_key:
        st.info('AI credentials detected. You can try recipe generation; provider access and billing must also be enabled.')
        if st.button('🪄 Generate my recipe', type='primary', key='generate_cloud'):
            st.session_state.generated = None
            with st.spinner('Creating your recipe...'):
                try:
                    st.session_state.generated = generate_recipe(
                        st.session_state.fridge,
                        diet=diet,
                        avoid=st.session_state.avoid,
                        minutes=max_minutes,
                        model='gpt-4o-mini',
                        api_key=api_key,
                    )
                except RecipeGenerationError as err:
                    st.error(str(err))
    else:
        st.info('AI generation is not enabled on this deployment. Use Discover recipes to browse the expanded catalog, or configure OPENAI_API_KEY in Streamlit Cloud Secrets to unlock experimental generation.')
        st.button('🪄 Generate my recipe', disabled=True, key='generate_cloud_disabled')

    if st.session_state.generated:
        generated = st.session_state.generated
        image_col, detail_col = st.columns([1.1, 1.9])
        with image_col:
            st.image(get_recipe_image({
                'name': generated['name'],
                'ingredients': generated['ingredients'],
                'tags': ['AI generated'],
                'minutes': generated['minutes'],
            }), use_container_width=True)
        with detail_col:
            st.markdown(f'### {generated["name"]}')
            st.write(generated['description'])
            st.markdown(
                f'<span class="mini-badge">⏱️ {generated["minutes"]} min</span>'
                f' <span class="mini-badge">AI generated</span>'
                f' <span class="mini-badge">Model: {generated["model"]}</span>',
                unsafe_allow_html=True,
            )
            if generated['missing']:
                st.warning('Additional ingredients needed: ' + ', '.join(generated['missing']))
            else:
                st.success('Great news: all ingredients in the generated recipe are already in your fridge list!')
            if generated['blocked']:
                st.error('Excluded ingredient detected: ' + ', '.join(generated['blocked']))
            for warning in generated['warnings']:
                st.warning(warning)
            st.markdown('**Ingredients:** ' + ', '.join(generated['ingredients']))
            st.markdown('**Instructions**')
            for i, step in enumerate(generated['steps'], 1):
                st.write(f'{i}. {step}')
            if generated['tips']:
                st.caption('Chef tip: ' + generated['tips'])
            st.caption('AI-generated recipes can make mistakes. Always check quantities, allergens, and food safety before cooking.')

with saved_tab:
    st.subheader('🛒 Saved recipes and shopping list')
    if not st.session_state.saved:
        st.info('Save recipes from the Discover tab to build your meal plan and shopping list.')
    else:
        saved_recipes = [r for r in all_recipes if r['name'] in st.session_state.saved]
        st.write('**Saved recipes:** ' + ', '.join(r['name'] for r in saved_recipes))
        fridge_set = set(parse_ingredients(st.session_state.fridge))
        missing_items = sorted({ing for recipe in saved_recipes for ing in recipe['ingredients'] if ing not in fridge_set})

        grid_cols = st.columns(2)
        for idx, recipe in enumerate(saved_recipes):
            with grid_cols[idx % 2]:
                st.image(get_recipe_image(recipe), use_container_width=True)
                st.markdown(f'**{recipe["name"]}**')
                st.caption(f'{recipe["minutes"]} min · ' + ', '.join(recipe['tags']))

        st.markdown('### Combined shopping list')
        if missing_items:
            for item in missing_items:
                st.checkbox(item, key=f'shopping_{item}')
            st.download_button(
                '⬇️ Download shopping list',
                data='\n'.join(missing_items) + '\n',
                file_name='fridgechef_shopping_list.txt',
                mime='text/plain',
            )
        else:
            st.success('You already have everything needed for your saved recipes!')

st.divider()
st.caption('FridgeChef AI is an educational proof-of-concept. Recipe recommendations come from a catalog combining an original curated set with template-derived variations, and optional recipe generation uses a local language model. Always verify allergens, dietary needs, quantities and cooking safety.')
