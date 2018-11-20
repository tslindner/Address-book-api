# Import dependencies
from datetime import datetime
from elasticsearch import Elasticsearch

from flask import Flask, render_template, redirect, request, jsonify
from flask_restful import Resource, Api

from pprint import pprint

import json

# Initialize elasticsearch
port = input('Enter elasticsearch port number (default 9200):')
if port == '':
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
    


def name_check(name):
    pprint(name)
    res = es.search(index=index_name, body={"query": {"term": {"name": name}}})
    print('this is the res')
    pprint(res)
    pprint(res['hits'])
    if res['hits']['total'] == 0:
        return True
    else:
        return False

def query_handler(get_query):
    res = es.search(index=index_name, body=get_query)
    return res

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


    print('this one')
    print(doc['name'])
    name_available = name_check(doc['name'])
    print(name_available)
    if name_available == True:
        try:
            post_outcome = es.index(index=index_name, doc_type='contacts', body=doc)
            print(post_outcome)
            return True, post_outcome
        except Exception as ex:
            print('Error in indexing data')
            print(str(ex))
            return False, f'Something went wrong, exception thrown'
    else:
        return False, 'Name unavailable'

def get_name(name):
    res = es.search(index=index_name, body={"query": {"match": {"name": f"{name}"}}})
    print(name)
    return res

def put_doc(name, doc):
    doc['name'] = doc['name'].lower().replace(" ", "")
    name_available = name_check(name)
    print('made it here')
    if name_available == True:
        return 'No entry by that name exists'
    else:
        try:
            initial_entry = get_name(name)
            pprint(initial_entry)
            initial_id = initial_entry['hits']['hits'][0]['_id']
            pprint(initial_id)
            res = es.update(index=index_name, doc_type='contacts', id=initial_id, body={"doc": doc})
            pprint(res)
            return f'Successfully updated {name}'
        except Exception as ex:
            print(str(ex))
            return 'Something went wrong, exception thrown'

def delete_doc(name):
    name_available = name_check(name)
    if name_available == True:
        return 'No entry by that name exists'
    else:
        try:
            initial_entry = get_name(name)
            initial_id = initial_entry['hits']['hits'][0]['_id']
            es.delete(index=index_name, doc_type='contacts', id=initial_id)
            return f'Successfully deleted {name}'
        except Exception as ex:
            print(str(ex))
            return 'Something went wrong, exception thrown'        



app = Flask(__name__)
api = Api(app)

@app.route('/contacts',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def home():
    name      = request.args.get('name') 
    page_size = request.args.get('pageSize') 
    page      = request.args.get('page') 
    query     = request.args.get('query') 
    body      = request.get_json()

    name = name.lower().replace(" ", "")
    

    if request.method == 'GET' and query:
        get_query = dict(page_size = page_size,
                        page      = page,
                        query     = query
        )
        print('this is a get query')

        res = query_handler(query)
        return jsonify(res)

    elif request.method == 'GET' and name:
        res = get_name(name)
        return jsonify(res)

    elif request.method == 'POST' and body:
        print('this is a post')
        success, post_outcome = post_name(body)
        pprint(post_outcome)
        if success:
            return 'Post successful'
        elif type(post_outcome) == dict:
            return 'Post failed, name already exists:'
        else: 
            return post_outcome

    elif request.method == 'PUT':
        if body and name:
            res = put_doc(name, body)
            return res
        else:
            return 'You must pass a name and an updated document with a PUT call.'


    elif request.method == 'DELETE':
        if name:
            res = delete_doc(name)
            return res
        else:
            return 'You must pass a name with a DELETE call'


    


# Populate db with mock data

with open('resources/generated.json') as f:
    data = json.load(f)

    for i in data[0:5]:
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


