import unittest
from jschemalite import match,sample_match

class SampleTest(unittest.TestCase):
    def test_onesided(self):
        schema = {'!minimum':0.5}
        for i in range(50):
            val = sample_match(schema)
            self.assertIsInstance(val,float)
            self.assertGreaterEqual(val,0.5)
            self.assertTrue(match(val,schema))
    
    def test_twosided(self):
        schema = {'!type':'int','!minimum':2,'!maximum':6}
        for i in range(50):
            val = sample_match(schema)
            self.assertIsInstance(val,int)
            self.assertGreaterEqual(val,2)
            self.assertLessEqual(val,6)
            self.assertTrue(match(val,schema))
        
    def test_list(self):
        schema = {'!type':'list','!minItems':2,'!maxItems':6,'!items':{'!type':'int','!minimum':2,'!maximum':6}}
        for i in range(50):
            val = sample_match(schema)
            self.assertIsInstance(val,list)
            self.assertGreaterEqual(len(val),2)
            self.assertLessEqual(len(val),6)
            for j in val:
                self.assertGreaterEqual(j,2)
                self.assertLessEqual(j,6)
            self.assertTrue(match(val,schema))

    def test_dict_template(self):
        obj = {'a':3,'b':{'foo':'bar','baz':[0.4,0.2]}}
        schema = {'a':None,'b':{'foo':None,'baz':None}}        #dict must have the top-level key structure 
        for i in range(5):
            val = sample_match(schema,obj)
            print(val)
            self.assertTrue(match(val,schema))
        schema2 = {'b':{'baz':[None,{'!minimum':0,'!maximum':0.2}]}}   #will pass this
        for i in range(5):
            val = sample_match(schema2,obj)
            self.assertTrue(match(val,schema2))
            print(val)
        schema3 = {'b':{'baz':[None,{'!minimum':0,'!exclusiveMaximum':0.2}]}}   #will fail this
        for i in range(5):
            val = sample_match(schema3,obj)
            print(val)
            self.assertTrue(match(val,schema3))

