"""JSON Schema Lite uses a JSON Schema-like syntax to match JSON objects.

Why use this instead of JSON Schema? 

First reason: It's *much* less verbose than JSON Schema.

Second reason: It's *way easier* to write rules!
Since rules largely match the JSON representation of an object, it's really 
simple to modify items to specify what you'd like.  Say that you want to match
a user login object, except for the 'session' and 'ip' key::

    item = {
        "name":"John Doe",
        "password":"john123",
        "session":28387432,
        "ip":"128.0.0.1"
    }

To ignore these keys, just set::

    schema = copy.copy(item)
    schema['session']=None
    schema['ip']=None

Then, the :func:`match` function will match any item matching John Doe's
record, except for the 'session' and 'ip' keys.

As another example, suppose that you'd like to recognize "large circles".  The
circle object is represented by an object like this::

    circle = {
        "type":"Circle",
        "center":[0.583,3.2919],
        "radius":0.25
    }

Then, we can simply modify some conditions the center and radius to match
circles with radius greater than 2::

    big_circle_schema = circle.copy()
    big_circle_schema['center'] = [None,None]  #match 2-element lists
    big_circle_schema['radius'] = {'!minimum':2}  #match any radius >= 2
    print(jschemalite.match(circle,big_circle_schema)) #prints False

Note that the 'center' key will match any 2-element list, including compound
objects like ``[{'a':3},[2,3,4]]``. If you really want to be specific that 
items need to be numeric, you can replace its rule with the JSON Schema-like
specifier::

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

Note that only a subset of JSON Schema is implemented.

Basic schema rules
------------------

- An object will always match itself. 
- ``None``: An object will always match with None.
- ``list``: The object must be a list of the same length as the rule.  Each 
  item must match the corresponding item in the rule.
- ``dict``: A dict rule states which keys must exist in the object, EXCEPT for
  special rules (i.e., keys prefixed with "!").  Each subkey's value must match
  the rule under the corresponding subkey in the dict.


Special rules
--------------

Special rules are always dicts, with keys prefixed with "!".  Special keys are
patterned after JSON Schema specifiers, and include the following:

- !type [str or list]: accept any object of this type. Accepts JSON Schema 
  "string", "number", "integer", "array", "object", "boolean", "null" as well
  as Python class names 'str', 'float', 'int', 'list', 'dict'. or 'bool'.

  If a list is given, multiple types are accepted.
- !enum list: accept any object that matches one of the items in the list. 
- !minimum value: accept numeric values that are >= value
- !maximum value: accept numeric values that are <= value
- !exclusiveMinimum value: accept numeric values that are > value
- !exclusiveMaximum value: accept numeric values that are < value
- !properties dict: designates a dict of possible properties (keys).
  The property name will map to its specification.  Note that like JSON Schema,
  properties are optional.
- !additionalProperties bool: if False, will not allow any other properties
  in a dictionary than are specified in the rule.
- !required list: a list of property names that are required.
- !minProperties value: must have at least this number of properties
- !minProperties value: must have at least this number of properties
- !items rule: for lists/arrays, all items must match this rule.  (Note: can't
  specify multiple item rules as in JSON Schema)
- !minItems value: lists/arrays must have at least this number of items.
- !maxItems value: lists/arrays must have at most this number of items.
- !anyOf list: any of the rules given in the list may match.
- !length value: length specifier, works for either dicts or lists.
- !or list: alias for anyOf.
- !value val: takes on value val.  Usually you'd want to just replace the
  dict with val, but for quick insertion of fixed values into an existing
  schema, this will do in a pinch.
- !empty: matches with nothing (not even None). Used to specify that a key
  should not be present in a dict.


Quirks
------

Tuples are treated as lists.

To specify that an item needs to be exactly `None`, you will need to use
the rule `{"!type":"null"}`.

Examples
---------

Basic examples::

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


Sampling
---------

We can also sample objects that match a schema using the :func:`sample_match`
function.  This works best when numeric items have a minimum and maximum.


Double-checking
---------------

Can convert to JSON Schema using :func:`to_json_schema`.

No conversions from JSON Schema back to JSON Schema Lite yet.


Wishlist
--------

- Projections onto schemas
- Intersections between schemas
- Auto-generation of schemas from data (I have something like this in the ikdb project)
- References to named schema rules like JSON-Schema.
- Schemas that refer to prior matched items, perform comparisons.

"""

from __future__ import print_function
import warnings

_json_typemap = {'integer':'int','number':'float','string':'str','boolean':'bool','array':'list','object':'dict'}
_python_typemap = {'int':'integer','float':'number','bool':'boolean','list':'array','tuple':'array','dict':'object'}

def _match_type(obj,rule,stack):
    global _json_typemap
    if isinstance(rule,str):
        if rule in _json_typemap:
            rule = _json_typemap[rule]
        if rule == 'null':
            return obj is None
        if isinstance(obj,tuple):
            return rule=='list' or rule=='tuple'
        return obj.__class__.__name__ == rule or (rule == 'float' and obj.__class__.__name__=='int')
    elif isinstance(rule,(list,tuple)):
        for type in rule:
            if _match_type(obj,type):
                return True
        return False
    raise ValueError("!type schema specifies invalid rule, must be str or list")

def _match_enum(obj,rule,stack):
    if isinstance(rule,(list,tuple)):
        return obj in rule
    raise ValueError("!enum schema specifies invalid rule, must be list")

def _match_minimum(obj,rule,stack,exclusive=False):
    if isinstance(rule,(int,float)):
        if not isinstance(obj,(int,float)):
            return False
        if exclusive:
            return rule < obj 
        return rule <= obj 
    if exclusive:
        raise ValueError("!exclusiveMinimum schema specifies invalid rule, must be number")
    raise ValueError("!minimum schema specifies invalid rule, must be number")

def _match_maximum(obj,rule,stack,exclusive=False):
    if isinstance(rule,(int,float)):
        if not isinstance(obj,(int,float)):
            return False
        if exclusive:
            return rule > obj 
        return rule >= obj 
    if exclusive:
        raise ValueError("!exclusiveMaximum schema specifies invalid rule, must be number")
    raise ValueError("!maximum schema specifies invalid rule, must be number")

def _match_properties(obj,rule,stack,additional=True):
    global _match_fail
    if isinstance(rule,dict):
        for k,v in rule.items():
            if k in obj:
                if stack is not None:
                    stack.append(k)
                if not match(obj[k],v,stack):
                    return False
                if stack is not None:
                    stack.pop(-1)
        if not additional:
            for k,v in obj.items():
                if k not in rule:
                    return False
        return True
    raise ValueError("!properties schema specifies invalid rule, must be dict")

def _match_required(obj,rule,stack):
    if isinstance(rule,list):
        if not isinstance(obj,dict):
            return False
        return all(k in obj for k in rule)
    raise ValueError("!required schema specifies invalid rule, must be list")

def _match_minProperties(obj,rule,stack):
    if isinstance(rule,int):
        if not isinstance(obj,dict):
            return False
        return len(obj) >= rule
    raise ValueError("!minProperties schema specifies invalid rule, must be integer")

def _match_maxProperties(obj,rule,stack):
    if isinstance(rule,int):
        if not isinstance(obj,dict):
            return False
        return len(obj) <= rule
    raise ValueError("!maxProperties schema specifies invalid rule, must be integer")

def _match_items(obj,rule,stack):
    if not isinstance(obj,list):
        return False
    for i,o in enumerate(obj):
        if stack is not None:
            stack.append(i)
        if not match(o,rule):
            return False
        if stack is not None:
            stack.pop(-1)
    return True

def _match_minItems(obj,rule,stack):
    if isinstance(rule,int):
        if not isinstance(obj,list):
            return False
        return len(obj) >= rule
    raise ValueError("!minItems schema specifies invalid rule, must be integer")

def _match_maxItems(obj,rule,stack):
    if isinstance(rule,int):
        if not isinstance(obj,list):
            return False
        return len(obj) <= rule
    raise ValueError("!maxItems schema specifies invalid rule, must be integer")

def _match_anyOf(obj,rule,stack):
    if isinstance(rule,list):
        return any(match(obj,i) for i in rule)
    raise ValueError("!anyOf schema specifies invalid rule, must be list")    

def _match_length(obj,rule,stack):
    if isinstance(rule,int):
        if not hasattr(obj,'__len__'):
            #print("jschemalite: trying to match !length with non-iterable",obj)
            return False
        return len(obj) == rule
    raise ValueError("!length schema specifies invalid rule, must be integer")

def _match_value(obj,rule,stack):
    return obj == rule

_matchers = {
    '!type':_match_type,
    '!enum':_match_enum,
    '!minimum':_match_minimum,
    '!maximum':_match_maximum,
    '!exclusiveMinimum':lambda obj,rule,stack:_match_minimum(obj,rule,stack,True),
    '!exclusiveMaximum':lambda obj,rule,stack:_match_maximum(obj,rule,stack,True),
    '!required':_match_required,
    '!minProperties':_match_minProperties,
    '!maxProperties':_match_maxProperties,
    '!items':_match_items,
    '!minItems':_match_minItems,
    '!maxItems':_match_maxItems,
    '!anyOf':_match_anyOf,
    '!length':_match_length,
    '!or':_match_anyOf,
    '!value':_match_value,
    '!empty':lambda obj,rule,stack:False
}

_dict_rules = set(['!properties','!additionalProperties','!minProperties','!maxProperties'])
_list_rules = set(['!items','!minItems','!minItems'])


def match(obj,schema,stack=None):
    """Returns True if the object matches the schema, and False otherwise.

    To receive information about the cause of a failed match, pass in an
    empty list into stack.  If False is returned, then the list will contain
    the path to the failed match.  Example::

        failure = []
        if match(obj,schema,failure):
            print("Failed match along path",failure)

    """
    global _matchers
    if schema is None:
        return True
    if isinstance(schema,dict):
        #parse for rules
        for (k,v) in schema.items():
            if k.startswith('!'):
                try:
                    matcher = _matchers[k]
                except KeyError:
                    if k=='!properties':
                        return _match_properties(obj,v,stack,schema.get('!additionalProperties',False))
                    elif k=='!additionalProperties':
                        continue
                    else:
                        raise ValueError("schema specifies invalid rule {}".format(k))
                if not matcher(obj,v,stack):
                    #print("Failed to match rule",k)
                    if stack is not None:
                        stack.append(k)
                    return False
            else:
                if not isinstance(obj,dict):
                    if stack is not None:
                        stack.append("!type")
                    #print("Not dict?")
                    return False
                if k not in obj:
                    if stack is not None:
                        stack.append(k)
                    #print("Missing",k)
                    return False
                if stack is not None:
                    stack.append(k)
                if not match(obj[k],v,stack):
                    #print("Failed to match on subkey",k)
                    return False
                if stack is not None:
                    stack.pop(-1)
    elif isinstance(schema,(list,tuple)):
        if not isinstance(obj,(list,tuple)):
            if stack is not None:
                stack.append("!type")
            #print("Didn't fit list/tuple schema")
            return False
        if len(schema) != len(obj):
            if stack is not None:
                stack.append("!length")
            #print("Invalid length")
            return False
        for i,(o,s) in enumerate(zip(obj,schema)):
            if stack is not None:
                stack.append(i)
            if not match(o,s,stack):
                #print("Element",i,"failed to match")
                return False
            if stack is not None:
                stack.pop(-1)
    else:
        if obj != schema:
            if stack is not None:
                stack.append("!value")
            #print("Raw element didn't match value")
            return False
    return True


def sample_match(schema,template=None):
    """Samples a random JSON-compatible object that matches the schema.

    If template is provided, it should be an object that matches the
    schema, and for any None rules its entries will be used in the result.
    Furthermore, for any optional dictionary entries, its values will be
    added to the result.

    Otherwise, the result will have None where a None rule is included,
    and no more properties than those defined in the schema.
    """
    import random
    if schema is None:
        return template
    if isinstance(schema,dict):
        res = dict()
        objtype = None
        minimum = None
        maximum = None
        exclusiveMinimum = False
        exclusiveMaximum = False
        for k,v in schema.items():
            if k.startswith('!'):
                if k == '!enum':
                    return random.sample(v)
                elif k == '!type':
                    if isinstance(v,str):
                        if v in _json_typemap:
                            v = _json_typemap[v]
                        if v=='int':
                            objtype = int
                        elif v=='float':
                            objtype = float
                        elif v=='str':
                            objtype = str
                        elif v=='list':
                            objtype = list
                        elif v=='dict':
                            objtype = dict
                        elif v=='bool':
                            objtype = bool
                        elif v=='null':
                            return None
                        else:
                            raise ValueError("Invalid schema type "+v)
                elif k == '!minimum':
                    minimum = v
                elif k == '!maximum':
                    maximum = v
                elif k == '!exclusiveMinimum':
                    minimum = v
                    exclusiveMinimum = True
                elif k == '!exclusiveMaximum':
                    maximum = v
                    exclusiveMaximum = True
                elif k=='!properties':
                    for prop,pschema in v.items():
                        if template is None:
                            res[prop] = sample_match(pschema)
                        else:
                            res[prop] = sample_match(pschema,template.get(prop,None))
                elif k=='!items':
                    if template is not None:
                        length = len(template)
                    else:
                        length = 1
                        if '!length' in schema:
                            length = schema['!length']
                        elif '!minItems' in schema and '!maxItems' in schema:
                            length = random.randint(schema['!minItems'],schema['!maxItems'])
                        elif '!minItems' in schema:
                            length = schema['!minItems']
                        elif '!maxItems' in schema:
                            length = schema['!maxItems']
                    if template is not None:
                        return [sample_match(v,template[i]) for i in range(length)]
                    else:
                        return [sample_match(v) for i in range(length)]
                elif k in ['!minItems','!maxItems','!minProperties','!maxProperties','!additionalRules','!length']:
                    pass
                elif k in ['!anyOf','!or']:
                    if template is not None:
                        #check to see which rules match?
                        pass
                    r = random.sample(v)
                    return sample_match(v,template)
                elif k == '!value':
                    return v
                else:
                    raise ValueError("schema specifies invalid rule {}".format(k))
            else:
                if template is None:
                    res[k] = sample_match(v)
                else:
                    res[k] = sample_match(v,template.get(k,None))
        if objtype is None:
            #min/max becomes float
            if minimum is not None or maximum is not None:
                objtype = float
            elif not isinstance(template,dict):
                return template
        if objtype is not None and objtype != dict:
            if objtype == bool:
                return random.choice([False,True])
            elif minimum is not None or maximum is not None:
                if minimum is not None and maximum is None:
                    maximum = minimum + 1
                if maximum is not None and minimum is None:
                    minimum = maximum - 1
                if objtype != int and objtype != float:
                    raise ValueError("Can't sample in a range for a non numeric object")
                if objtype == int:
                    if exclusiveMinimum:
                        minimum += 1
                    if exclusiveMaximum:
                        maximum -= 1
                    return random.randint(minimum,maximum)
                else:
                    iters = 0
                    while True:
                        v = random.uniform(minimum,maximum)
                        if (not exclusiveMinimum or v > minimum) and (not exclusiveMaximum or v < maximum):
                            return v
                        if maximum <= minimum:
                            return v
                        iters += 1
                        if iters > 10:
                            warnings.warn("Huh... random sampling never got an item within bounds?")
                            return v
            else:
                return objtype()
        if template is not None:
            for k,v in template.items():
                if k not in res:
                    res[k] = v
        return res
    elif isinstance(schema,(list,tuple)):
        if template is not None:
            if len(template) != len(schema):
                raise ValueError("Invalid template provided, not the right length")
            return [sample_match(s,t) for (s,t) in zip(schema,template)]
        else:
            return [sample_match(s) for s in schema]
    else:
        return schema

def to_json_schema(schema):
    """Translates a (light) schema to proper JSON-Schema.
    """
    res = _to_json_schema(schema)
    res["$schema"] = "http://json-schema.org/draft/2019-09/schema#"
    return res

def _to_json_schema(schema):
    if schema is None:
        return {}
    if isinstance(schema,dict):
        res = {}
        required = {}
        for (k,v) in schema.items():
            if k.startswith('!'):
                if k=='!type':
                    if v in _python_typemap:
                        res['type'] = _python_typemap[v]
                    else:
                        res['type'] = v
                elif k=='!length':
                    res['minItems'] = v
                    res['maxItems'] = v
                elif k=='!or' or k=='!anyOf':
                    res['anyOf'] = [_to_json_schema(rule) for rule in v]
                elif k=='!value':
                    return {'const':v}
                else:
                    res[k[1:]] = v
            else:
                required[k] = _to_json_schema(v)
        if 'type' not in res:
            if any(k in _dict_rules for k in schema.keys()):
                res['type'] = 'object'
            if any(k in _list_rules for k in schema.keys()):
                if 'type' in res:
                    warnings.warn("Mixture of dict and list rules in schema?")
                res['type'] = 'list'

        if required:
            res['type'] = 'object'
            res['required'] = list(required.keys())
            if 'properties' not in res:
                res['properties'] = {}
            res['properties'].update(required)
        return res
    elif isinstance(schema,(list,tuple)):
        items = []
        for item in schema:
            items.append(_to_json_schema(item))
        res = {'type':'array','items':items,'additionalItems':False}
        return res
    else:
        return {'const':schema}


