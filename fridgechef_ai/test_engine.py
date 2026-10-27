import unittest
from engine import parse_ingredients, recommend, load_recipes

class EngineTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(parse_ingredients('Eggs, tomatoes, spaghetti'),['egg','tomato','pasta'])
    def test_exact_recipe_first(self):
        result=recommend('egg, tomato, cheese, milk, butter',max_missing=5)
        self.assertEqual(result[0]['name'],'Tomato & Cheese Omelette')
        self.assertTrue(result[0]['ready'])
    def test_separate_ready_and_missing(self):
        result=recommend('bread, cheese',max_missing=5)
        self.assertTrue(result[0]['ready'])
        self.assertEqual(result[0]['name'],'Cheese Toast')
    def test_no_wrong_milk_alias(self):
        result=recommend('soy milk, egg, tomato, cheese, butter',only_ready=True)
        self.assertFalse(any(r['name']=='Tomato & Cheese Omelette' for r in result))
    def test_pantry_opt_in(self):
        result=recommend('pasta, tomato, garlic',only_ready=True,pantry_staples=True)
        self.assertTrue(any(r['name']=='Tomato Garlic Pasta' for r in result))
    def test_vegan(self):
        result=recommend('chickpea, tomato, onion, coconut milk, curry powder',diet='Vegan',max_missing=0)
        self.assertTrue(result)
        self.assertTrue(all('vegan' in x['tags'] for x in result))
    def test_blank(self):
        self.assertEqual(recommend(''),[])
    def test_avoid_ingredient(self):
        results=recommend('egg, tomato, cheese, milk, butter',exclude='egg')
        self.assertTrue(all('egg' not in r['ingredients'] for r in results))
    def test_ranking_options(self):
        for priority in ['Closest match','Use more of my ingredients','Fastest cooking']:
            self.assertTrue(recommend('egg, tomato, cheese, milk, butter',priority=priority))
    def test_all_data(self):
        for r in load_recipes():
            self.assertTrue(r['ingredients'] and r['steps'])
if __name__=='__main__': unittest.main()
