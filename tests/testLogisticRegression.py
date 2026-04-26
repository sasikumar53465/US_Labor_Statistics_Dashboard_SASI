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
        if "#si-logistic-regression" in j:
            exec(compile("".join(i['source']), '<string>', 'exec'))


# todo: replace this with an actual test
class TestCase(unittest.TestCase):

    def testDepVar(self):
        self.assertTrue(reg.model.endog_names=='G3', "Your dependent variable isn't 'G3'!")

    def testLogitFitted(self):
        self.assertTrue(bool(re.search(r'BinaryResultsWrapper', str(type(reg)))), "You didn't fit your logit model.")

    def testLogit(self):
        self.assertTrue(bool(re.search(r'Logit', str(type(reg.model)))), "You didn't create a logit model.")

  