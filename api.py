# Import dependencies
from datetime import datetime
from elasticsearch import Elasticsearch

from flask import Flask, render_template, redirect, request, jsonify
from flask_restful import Resource, Api

from pprint import pprint

import json

# Initialize elasticsearch
# port = input('Enter elasticsearch port number (default 9200):')
# if port == '':
#     port = 9200

port = 9200

es = Elasticsearch(HOST='http://localhost', PORT=port)
index_name = 'address_book'


def create_index(es):
    created = False
    # index settings
    settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "contacts": {
                "dynamic": "strict",
                "properties": {
                    "name": {
                        "type": "text"
                    },
                    "phone": {
                        "type": "long"
                    },
                    "address": {
                        "type": "text"
                    },
                    "city": {
                        "type": "text"
                    },
                    "state": {
                        "type": "text"
                    },
                    "zip": {
                        "type": "long"
                    }
                }
            }
        }
    }
    try:
        if not es.indices.exists(index_name):
            es.indices.create(index=index_name, ignore=400, body=settings)
            print('Created Index')
        created = True
    except Exception as ex:
        print(str(ex))
    finally:
        return created
es.indices.delete(index_name)
create_index(es)

def body_cleaner(body):

    formatting = True

    keys_to_be_deleted = []

    for key, value in body.items():
        if body[key] is None:
            keys_to_be_deleted.append(key)
            continue
        elif key == 'phone':
            body[key] = str(body[key])
            if len(body['phone']) != 10:
                formatting = False
        elif key == 'zip':
            body[key] = str(body[key])
            if len(body['zip'])   >  10:
                formatting = False
        else:
            body[key] = body[key].lower().replace(' ', '')
            if body[key].isalpha() == False:
                formatting = False

    for key in keys_to_be_deleted:
        del body[key]

    if formatting == False:
        return 'Input was formatted incorrectly'

    else:
        return body
    



    # name = body['name']
    # phone = body['phone']
    # address = body['address']
    # city = body['city']
    # state = body['state']
    # _zip = body['zip']

    # name = name.lower().replace(" ", "")
    # address = address.lower().replace(" ", "")
    # city = city.lower().replace(" ", "")
    # state = state.lower().replace(" ", "")
    # phone = str(phone)
    # _zip = str(_zip)

    # if (
    #     name.isalpha()  == False or
    #     len(phone)      != 10    or
    #     city.isalpha()  == False or
    #     state.isalpha() == False or
    #     len(_zip)       >  10
    # ):
    #     return "Input improperly formatted"

    # else:
    #     body['name'] = name
    #     body['phone'] = phone
    #     body['address'] = address
    #     body['city'] = city
    #     body['state'] = state
    #     body['zip'] = _zip

    # return body
    


def get_id(name):
    res = es.search(index=index_name, body={"query": {"term": {"name": name}}})
    print(name)
    pprint(res)
    if res['hits']['total'] > 0:
        return res['hits']['hits'][0]['_id']
    else:
        return False

# def query_handler(get_query):
#     res = es.search(index=index_name, body=get_query)
#     return res

def post_name(doc):

    name = doc['name']
    phone = doc['phone']
    address = doc['address']
    city = doc['city']
    state = doc['state']
    _zip = doc['zip']

    name = name.lower().replace(" ", "")
    address = address.lower().replace(" ", "")
    city = city.lower().replace(" ", "")
    state = state.lower().replace(" ", "")
    phone = str(phone)
    _zip = str(_zip)

    if (
        name.isalpha()  == False or
        len(phone)      != 10    or
        city.isalpha()  == False or
        state.isalpha() == False or
        len(_zip)       >  10
    ):
        return "Input improperly formatted"

    else:
        doc['name'] = name
        doc['phone'] = phone
        doc['address'] = address
        doc['city'] = city
        doc['state'] = state
        doc['zip'] = _zip



    name_id = get_id(doc['name'])
    if name_id == False:
        try:
            post_outcome = es.index(index=index_name, doc_type='contacts', body=doc)
            return True, post_outcome
        except Exception as ex:
            print('Error in indexing data')
            print(str(ex))
            return False, f'Something went wrong, exception thrown'
    else:
        return False, 'Name unavailable'

def get_name(name):
    res = es.search(index=index_name, body={"query": {"match": {"name": f"{name}"}}})
    return res

# def put_doc(name, doc):
#     doc['name'] = doc['name'].lower().replace(" ", "")
#     name_available = name_check(name)
#     print('made it here')
#     if name_available == True:
#         return 'No entry by that name exists'
#     else:
#         try:
#             initial_entry = get_name(name)
#             pprint(initial_entry)
#             initial_id = initial_entry['hits']['hits'][0]['_id']
#             pprint(initial_id)
#             res = es.update(index=index_name, doc_type='contacts', id=initial_id, body={"doc": doc})
#             pprint(res)
#             return f'Successfully updated {name}'
#         except Exception as ex:
#             print(str(ex))
#             return 'Something went wrong, exception thrown'

# def delete_doc(name):
#     name_available = name_check(name)
#     if name_available == True:
#         return 'No entry by that name exists'
#     else:
#         try:
#             initial_entry = get_name(name)
#             initial_id = initial_entry['hits']['hits'][0]['_id']
#             es.delete(index=index_name, doc_type='contacts', id=initial_id)
#             return f'Successfully deleted {name}'
#         except Exception as ex:
#             print(str(ex))
#             return 'Something went wrong, exception thrown'        



app = Flask(__name__)
api = Api(app)


@app.route('/contacts',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def home():

    param_dict =    body_cleaner(dict(  
                    name      = request.args.get('name'),
                    phone     = request.args.get('phone'),
                    address   = request.args.get('address'),
                    city      = request.args.get('city'),
                    state     = request.args.get('state'),
                    zip       = request.args.get('zip')))

    if isinstance(param_dict, str):
        return param_dict

    # query     = request.args.get('query') I don't understand how to get this to work.
    page_size = request.args.get('pageSize')
    page      = request.args.get('page') 
    body      = body_cleaner(request.get_json())

    try:
        page_size = int(page_size)
        page      = int(page)
    except Exception as ex:
        print('page and page_size must be integers')
        return 'page and page_size must be integers'

    if page_size is None:
        page_size = 50

    if page is None:
        page = 1


    if request.method == 'GET' and len(param_dict.items()) == 0:

        match_all_doc = {
                'size' : 10000,
                'query': {
                    'match_all' : {}
                }
            }
        res = es.search(index=index_name, doc_type='contacts', body=match_all_doc)

        first_doc = page_size * (page - 1)
        last_doc  = page_size * page

        return jsonify(res['hits']['hits'][first_doc:last_doc])

    elif request.method == 'GET':
        query_list = []

        for key, value in param_dict.items():
            if param_dict[key]:
                query_list.append({"term": {key : value}})

        res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})
        pprint(res)
        return jsonify(res)

    elif request.method == 'POST' and body:
        name_id = get_id(body['name'])
        print(name_id)
        if name_id == False:
            try:
                post_outcome = es.index(index=index_name, doc_type='contacts', body=body)
                return "Post Successfull"
            except Exception as ex:
                print('Error in indexing data')
                print(str(ex))
                return 'Something went wrong, exception thrown, POST aborted'
        else:
            return 'Name unavailable, POST aborted'

    elif request.method == 'PUT':
        if body and name:
            body['name'] = body['name'].lower().replace(" ", "")
            name_id = get_id(name)
            print('made it here')
            if name_id:
                try:
                    initial_entry = get_name(name)
                    initial_id = initial_entry['hits']['hits'][0]['_id']
                    res = es.update(index=index_name, doc_type='contacts', id=initial_id, body={"doc": body})
                    return f'Successfully updated {name}'
                except Exception as ex:
                    print(str(ex))
                    return 'Something went wrong, exception thrown, PUT aborted'
            else:
                return 'No entry by that name exists, PUT aborted'
            return res
        else:
            return 'You must pass a name and an updated document when passing a PUT call.'


    elif request.method == 'DELETE':
        if name:
            name_id = get_id(name)
            if name_id:
                try:
                    es.delete(index=index_name, doc_type='contacts', id=name_id)
                    return f'Successfully deleted {name}'
                except Exception as ex:
                    print(str(ex))
                    return 'Something went wrong, exception thrown, DELETE aborted'  
            else:
                return 'No entry by that name exists, DELETE aborted'
        else:
            return 'You must pass a name when passing a DELETE call'


    


# Populate db with mock data

with open('resources/generated.json') as f:
    data = json.load(f)

    for i in data:
        name = i['name']
        phone = i['phone']
        address = i['address']
        city = i['city']
        state = i['state']
        _zip = i['zip']

        name = name.lower().replace(" ", "")
        address = address.lower().replace(" ", "")
        city = city.lower().replace(" ", "")
        state = state.lower().replace(" ", "")
        


        post_name(i)


# Mock JSON created with https://www.json-generator.com/

# Generator code used:

# [
#   '{{repeat(125, 125)}}',
#   {
#     name: '{{firstName()}} {{surname()}}',
#     phone: '{{integer(1000000000, 9999999999)}}',
#     address: '{{integer(100, 999)}} {{street()}}',
#     city: '{{city()}}',
#     state: '{{state()}}',
#     zip: '{{integer(100, 10000)}}'
    
#     }
# ]




if __name__ == '__main__':
    app.run(debug=True)


