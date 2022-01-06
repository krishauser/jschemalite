import unittest
from jschemalite import match

obj = {'a':3,'b':{'foo':'bar','baz':[0.4,0.2]}}

class MatchTest(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(match(obj,obj))

    def test_none(self):
        schema1 = {'a':None,'b':None}       #dict must have keys 'a' and 'b'
        schema2 = {'a':None,'b':{'foo':None,'baz':None}}        #dict must have the top-level key structure 
        schema3 = {'b':{'foo':None}}                            #dict must have at least as many keys as are specified
        self.assertTrue(match(obj,schema1))
        self.assertTrue(match(obj,schema2))
        self.assertTrue(match(obj,schema3))
    
    def test_properties(self):
        schema1 = {'!properties':{'a':None,'b':None,'c':None}}  #dict may have keys 'a', 'b', and 'c'
        schema2 = {'b':{'baz':[None,{'!minimum':0,'!maximum':0.2}]}}   #will pass this
        schema3 = {'b':{'baz':[None,{'!minimum':0,'!exclusiveMaximum':0.2}]}}   #will fail this
        schema4 = {'!minProperties':2,'!maxProperties':3}
        schema5 = {'!minProperties':3,'!maxProperties':4}   #will fail this
        self.assertTrue(match(obj,schema1))
        self.assertTrue(match(obj,schema2))
        self.assertFalse(match(obj,schema3))
        stack = []
        match(obj,schema3,stack)
        self.assertTrue(len(stack) > 0)
        self.assertTrue(stack[-1] == '!exclusiveMaximum')
        print("Failure of",obj,"to match",schema3,"at",stack)
        self.assertTrue(match(obj,schema4))
        self.assertFalse(match(obj,schema5))
        stack = []
        match(obj,schema5,stack)
        self.assertTrue(len(stack) > 0)
        self.assertTrue(stack[-1] == '!minProperties')
        print("Failure of",obj,"to match",schema5,"at",stack)

    def test_types(self):
        array_schema = {'!type':'array'}    #object must be an array
        size2_array_schema = {'!type':'array','!length':2}    #object must be a length-2 array
        self.assertTrue(match(obj['b']['baz'],size2_array_schema))  #it's a length 2 array
        self.assertFalse(match(obj,array_schema))  #it's not an array
        stack = []
        match(obj,array_schema,stack)
        self.assertTrue(len(stack) > 0)
        self.assertTrue(stack[-1] == '!type')
        print("Failure of",obj,"to match",array_schema,"at",stack)
    
    def test_enum(self):
        enum_schema = {'!anyOf':["One","Two",{'!type':'list','!length':2}]}
        self.assertTrue(match("One",enum_schema))
        self.assertFalse(match([1],enum_schema))
        self.assertTrue(match([1,2],enum_schema))

