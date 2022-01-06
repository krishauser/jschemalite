# JSON Schmea Lite
## Author: Kris Hauser

JSON Schema Lite uses a JSON Schema-like syntax to match JSON objects.
Currently only available in Python.

Installation:

> pip install jschemalite

## Motivation

Why use this instead of JSON Schema? 

First reason: It's *much* less verbose than JSON Schema.

Second reason: It's *way easier* to write rules!
Since rules largely match the JSON representation of an object, it's really 
simple to modify items to specify what you'd like.  Say that you want to match
a user login object, except for the 'session' and 'ip' key:

```python
item = {
    "name":"John Doe",
    "password":"john123",
    "session":28387432,
    "ip":"128.0.0.1"
}
```

To ignore these keys, just set:

```python
schema = copy.copy(item)
schema['session']=None
schema['ip']=None
```

Then, the `match` function will match any item matching John Doe's
record, except for the 'session' and 'ip' keys.

As another example, suppose that you'd like to recognize "large circles".  The
circle object is represented by an object like this:

```python
circle = {
    "type":"Circle",
    "center":[0.583,3.2919],
    "radius":0.25
}
```

Then, we can simply modify some conditions the center and radius to match
circles with radius greater than 2:

```python
import jschemalite
big_circle_schema = circle.copy()
big_circle_schema['center'] = [None,None]  #match 2-element lists
big_circle_schema['radius'] = {'!minimum':2}  #match any radius >= 2
print(jschemalite.match(circle,big_circle_schema)) #prints False
```

Note that the `'center'` key will match any 2-element list, including compound
objects like `[{'a':3},[2,3,4]]`. If you really want to be specific that 
items need to be numeric, you can replace its rule with the JSON Schema-like
specifier::

```python
{
    '!type':'list',   #can use Python names or JSON names
    '!minItems':2,
    '!maxItems':2,
    '!items':{
        '!type':'number',
        '!minimum':-1000000,
        '!maximum':1000000
        }
}
```

Note that only a subset of JSON Schema is implemented.

## Basic schema rules

- An object will always match itself. 
- ``None``: An object will always match with None.
- ``list``: The object must be a list of the same length as the rule.  Each 
  item must match the corresponding item in the rule.
- ``dict``: A dict rule states which keys must exist in the object, EXCEPT for
  special rules (i.e., keys prefixed with "!").  Each subkey's value must match
  the rule under the corresponding subkey in the dict.


## Special rules

Special rules are always dicts, with keys prefixed with "!".  Special keys are
patterned after JSON Schema specifiers, and include the following:

- `!type` [str or list]: accept any object of this type. Accepts JSON Schema 
  "string", "number", "integer", "array", "object", "boolean", "null" as well
  as Python class names 'str', 'float', 'int', 'list', 'dict'. or 'bool'.

  If a list is given, multiple types are accepted.
- `!enum` list: accept any object that matches one of the items in the list. 
- `!minimum` value: accept numeric values that are >= value
- `!maximum` value: accept numeric values that are <= value
- `!exclusiveMinimum` value: accept numeric values that are > value
- `!exclusiveMaximum` value: accept numeric values that are < value
- `!properties` dict: designates a dict of possible properties (keys).
  The property name will map to its specification.  Note that like JSON Schema,
  properties are optional.
- `!additionalProperties` bool: if False, will not allow any other properties
  in a dictionary than are specified in the rule.
- `!required` list: a list of property names that are required.
- `!minProperties` value: must have at least this number of properties
- `!minProperties` value: must have at least this number of properties
- `!items` rule: for lists/arrays, all items must match this rule.  (Note: can't
  specify multiple item rules as in JSON Schema)
- `!minItems` value: lists/arrays must have at least this number of items.
- `!maxItems` value: lists/arrays must have at most this number of items.
- `!anyOf` list: any of the rules given in the list may match.
- `!length` value: length specifier, works for either dicts or lists.
- `!or` list: alias for ~!anyOf`.
- `!value` val: takes on value val.  Usually you'd want to just replace the
  dict with val, but for quick insertion of fixed values into an existing
  schema, this will do in a pinch.
- `!empty`: matches with nothing (not even None). Used to specify that a key
  should not be present in a dict.


## Quirks

Tuples are treated as lists.

To specify that an item needs to be exactly `None`, you will need to use
the rule `{"!type":"null"}`.

## Examples

Basic examples:

```python
from jschemalite import match

obj = {'a':3,'b':{'foo':'bar','baz':[0.4,0.2]}}
schema1 = {'a':None,'b':None}       #dict must have keys 'a' and 'b'
schema2 = {'!properties':{'a':None,'b':None,'c':None}}  #dict may have keys 'a', 'b', and 'c'
schema3 = {'a':None,'b':{'foo':None,'baz':None}}        #dict must have the top-level key structure 
schema4 = {'b':{'foo':None}}                            #dict must have at least as many keys as are specified
array_schema = {'!type':'array'}    #object must be an array
size2_array_schema = {'!type':'array','!length':2}      #object must be a length-2 array
print(match(obj,obj),"= True")  #an object matches itself
print(match(obj,schema1),"= True")  #it matches the schema
print(match(obj,schema2),"= True")  #it matches the schema
print(match(obj,schema3),"= True")  #it matches the schema
print(match(obj,schema4),"= True")  #it matches the schema
print(match(obj,array_schema),"= False")  #it's not an array
print(match(obj['b']['baz'],size2_array_schema),"= True")  #it's a length 2 array
enum_schema = {'!enum':["One","Two","Three"]}        #this is how you specify an enum
print(match("One",enum_schema))
print(match([1],enum_schema))
```

## Sampling

We can also sample objects that match a schema using the `sample_match`
function.  This works best when numeric items have a minimum and maximum.


## Conversions

Can convert to JSON Schema using `to_json_schema`.

No conversions from JSON Schema back to JSON Schema Lite yet.

JSON Schema Lite objects can be converted to MongoDB queries.

```python
from jschemalite.mongodb import jschemalite_to_mongodb
mongodb_query = jschemalite_to_mongodb(jsl_query)
```


## Wishlist

- Projections onto schemas
- Intersections between schemas
- Auto-generation of schemas from data (I have something like this in the ikdb project)
- References to named schema rules like JSON Schema.
- Schemas that refer to prior matched items, perform comparisons.

## Version history

0.1 (1/6/2021): first release
