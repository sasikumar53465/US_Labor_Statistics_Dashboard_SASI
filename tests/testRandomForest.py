import unittest
import json
import pandas as pd
import re

with open("Lesson.ipynb", "r") as file:
    f_str = file.read()

doc = json.loads(f_str)

code = [i for i in doc['cells'] if i['cell_type']=='code']
si = {}
for i in code:
    for j in i['source']:
        if "#si-random-forest" in j:
            exec(compile("".join(i['source']), '<string>', 'exec'))


# todo: replace this with an actual test
class TestCase(unittest.TestCase):
    def testForest(self):
        self.assertTrue(bool(re.search(r'RandomForestClassifier', str(type(playoffForest)))), "You didn't make a random forest!")

    def testForestFitted(self):
        self.assertTrue(hasattr(playoffForest, 'classes_'), "You didn't train your random forest!")

    def testDepVar(self):
        self.assertTrue('Playoffs' in y2.design_info.term_names, "'Playoffs' should be your dependent variable.")
