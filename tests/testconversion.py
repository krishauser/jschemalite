
import unittest
import json
import jsonschema
from jschemalite import to_json_schema

obj = {'a':3,'b':{'foo':'bar','baz':[0.4,0.2]}}

class JSONSchemaTest(unittest.TestCase):
    def test_jsonschema(self):
        js = to_json_schema(obj)
        jsonschema.validate(obj,js)
        schema1 = {'a':None,'b':None}       #dict must have keys 'a' and 'b'
        schema2 = {'!minProperties':2,'!maxProperties':3}
        schema3 = {'!minProperties':3,'!maxProperties':4}  #will fail this
        size2_array_schema = {'!type':'array','!length':2}    #object must be a length-2 array
        js = to_json_schema(schema1)
        jsonschema.validate(obj,js)
        js = to_json_schema(schema2)
        jsonschema.validate(obj,js)
        js = to_json_schema(schema3)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(obj,js)
        js = to_json_schema(size2_array_schema)
        jsonschema.validate(obj['b']['baz'],js)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(obj,js)


