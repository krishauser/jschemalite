"""Utility function for converting JSON-Schema-Lite directives to MongoDB
queries.

Note: not tested thoroughly yet.
"""

_jschemalite_directives_to_mongodb = {
    '!enum':'$in',
    '!minimum':'$gte',
    '!maximum':'$lte',
    '!exclusiveMinimum':'$gt',
    '!exclusiveMaximum':'$lt',
    '!required':lambda v:dict((k,{'$exists':True}) for k in v),
    '!minProperties':lambda v:{'$size':{'$gte':v}},
    '!maxProperties':lambda v:{'$size':{'$lte':v}},
    '!minItems':lambda v:{'$size':{'$gte':v}},
    '!maxItems':lambda v:{'$size':{'$lte':v}},
    '!anyOf':lambda v:{'$or':[jschemalite_to_mongodb(k) for k in v]},
    '!length':lambda v:{'$size':v},
    '!or':lambda v:{'$or':[jschemalite_to_mongodb(k) for k in v]},
    '!empty':lambda v:dict((k,{'$exists':False}) for k in v)
}

def _jschemalite_to_mongodb(schema):
    """Converts a jschemalite schema to mongodb query"""
    if isinstance(schema,dict):
        clauses = []
        res = {}
        for (k,v) in schema.items():
            if k[0] == '!':
                if k == '!type':
                    continue  #ignore
                elif k in _jschemalite_directives_to_mongodb:
                    newk = _jschemalite_directives_to_mongodb[k]
                    if callable(newk):
                        clauses.append(newk(v))
                    else:
                        clauses.append({newk,v})
                elif k == '!items':
                    raise ValueError("Cannot match queries on array !items")
                else:
                    raise ValueError("Invalid schema directive {}".format(k))
            else:
                res[k] = _jschemalite_to_mongodb(v)
        if clauses:
            if len(clauses)==1:
                return clauses[0]
            else:
                return {'$and',clauses}
        return res
    elif isinstance(schema,(list,tuple)):
        return [_jschemalite_to_mongodb(v) for v in schema]
    else:
        return schema

def _flatten(query):
    if isinstance(query,dict):
        res = {}
        for (k,v) in query.items():
            v = _flatten(v)
            if isinstance(v,dict):
                for (kv,vv) in v.items():
                    res['{}.{}'.format(k,kv)] = vv
            else:
                res[k] = v
        return res
    elif isinstance(query,(list,tuple)):
        res = {}
        for i,v in enumerate(query):
            v = _flatten(v)
            if isinstance(v,dict):
                for (kv,vv) in v.items():
                    res['{}.{}'.format(i,kv)] = vv
            else:
                res[str(i)] = v
    else:
        return query

def jschemalite_to_mongodb(schema):
    """Converts a jschemalite schema to mongodb query format."""
    res = _jschemalite_to_mongodb(schema)
    return _flatten(res)
