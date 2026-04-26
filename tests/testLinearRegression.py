import unittest
import json
import pandas
import re


with open("Lesson.ipynb", "r") as file:
    f_str = file.read()

doc = json.loads(f_str)

code = [i for i in doc['cells'] if i['cell_type']=='code']
si = {}
for i in code:
    for j in i['source']:
        if "#si-linear-regression" in j:
            exec(compile("".join(i['source']), '<string>', 'exec'))


# todo: replace this with an actual test
class TestCase(unittest.TestCase):

    def testDataImport(self):
        self.assertTrue(bool(re.search(r'log_wage', str(data.columns))), "'log_wage' should be your dependent variable.")

    def testRegression(self):
        self.assertTrue(bool(re.search(r'linear_model', str(type(reg)))), "Did you make a regression model?")