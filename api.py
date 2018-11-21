# Import dependencies
from datetime import datetime
from elasticsearch import Elasticsearch

from flask import Flask, render_template, redirect, request, jsonify
from flask_restful import Resource, Api

from pprint import pprint

import json

from modules.index_builder import create_index, get_id, body_cleaner, populate_index

# def get_id(es, param_dict, index_name):

#     query_list = []

#     for key, value in param_dict.items():
#         if param_dict[key]:
#             query_list.append({"term": {key : value}})

#     res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})

#     if res['hits']['total'] and res['hits']['total'] > 0:
#         _id  = res['hits']['hits'][0]['_id']
#         name = res['hits']['hits'][0]['_source']['name']
#         return _id, name
#     else:
#         return False

# Initialize elasticsearch
# port = input('Enter elasticsearch port number (default 9200):')
# if port == '':
#     port = 9200

port = 9200

es = Elasticsearch(HOST='http://localhost', PORT=port)
index_name = 'address_book'


es.indices.delete(index_name)
create_index(es, index_name)
populate_index('resources/generated.json', es, index_name)



app = Flask(__name__)
api = Api(app)

@app.route('/restart_index')
def restart():
    es.indices.delete(index_name)
    create_index(es, index_name)
    populate_index('resources/generated.json', es, index_name)

    return 'Index populated'


@app.route('/contact',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def contact():

    param_dict =    body_cleaner(dict(  
                    name      = request.args.get('name'),
                    phone     = request.args.get('phone'),
                    address   = request.args.get('address'),
                    city      = request.args.get('city'),
                    state     = request.args.get('state'),
                    zip       = request.args.get('zip')))

    if isinstance(param_dict, str):
        return param_dict

    try:
        body = body_cleaner(request.get_json())
    except Exception as ex:
        body = None
        print('No JSON body included')
        print(str(ex))

    # query     = request.args.get('query') I don't understand how to get this to work.
    page_size = request.args.get('pageSize')
    page      = request.args.get('page') 


    if page_size:
        try:
            page_size = int(page_size)
        except Exception as ex:
            print('page and pageSize must be integers')
            return 'page and pageSize must be integers'
    else:
        page_size = 10000

    if page:
        try:
            page = int(page)
        except Exception as ex:
            print('page and pageSize must be integers')
            return 'page and pageSize must be integers'
    else:
        page = 1

    if request.method == 'GET' and len(param_dict.items()) == 0:

        match_all_doc = {
                'size' : 10000,
                'query': {
                    'match_all' : {}
                }
            }
        res = es.search(index=index_name, doc_type='contact', body=match_all_doc)

        first_doc = page_size * (page - 1)
        last_doc  = page_size * page


        res = [doc['_source'] for doc in res['hits']['hits'] if isinstance(res['hits']['hits'], list)]
        return jsonify(res[first_doc:last_doc])


    elif request.method == 'GET':
        query_list = []

        for key, value in param_dict.items():
            if param_dict[key]:
                query_list.append({"term": {key : value}})

        res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})
        res = [doc['_source'] for doc in res['hits']['hits'] if isinstance(res['hits']['hits'], list)]
        pprint(res)
        return jsonify(res)

    elif request.method == 'POST':
        if body is not None:
            pprint(body)
            temp_name = {'name': body['name']}
            name_id, name = get_id(es, temp_name, index_name)
            if name_id == False:
                try:
                    es.index(index=index_name, doc_type='contact', body=body)
                    return f"Post Successfull.  A record for {name} has been created"
                except Exception as ex:
                    print('Error in indexing data')
                    print(str(ex))
                    return f'Something went wrong, exception thrown. POST aborted, {name} already exists'
            else:
                return f'Name unavailable. POST aborted, {name} already exists'
        else:
            return 'No JSON body included'

    elif request.method == 'PUT':
        print('here')
        if body and len(param_dict.items()) != 0:
            pprint(body)
            name_id, name= get_id(es, param_dict, index_name)
            if name_id:
                try:
                    res = es.update(index=index_name, doc_type='contact', id=name_id, body={"doc": body})
                    return f'Successfully updated {name}'
                except Exception as ex:
                    print(str(ex))
                    return f'Something went wrong, exception thrown. PUT aborted, {name} has not been updated'
            else:
                return f'No entry by that name exists. PUT aborted, {name} has not been updated'
            # return jsonify(res['hits']['hits'])
        else:
            return f'You must pass a name and an updated document when passing a PUT call. PUT aborted'


    elif request.method == 'DELETE':
        if len(param_dict.items()) != 0:
            name_id, name= get_id(es, param_dict, index_name)
            if name_id:
                try:
                    es.delete(index=index_name, doc_type='contact', id=name_id)
                    return f'Successfully deleted {name}'
                except Exception as ex:
                    print(str(ex))
                    return f'Something went wrong, exception thrown. DELETE aborted, {name} has not been deleted'  
            else:
                return f'No entry by that name exists. DELETE aborted, {name} has not been deleted'
        else:
            return f'You must pass a name when passing a DELETE call. DELETE aborted, {name} has not been deleted'




if __name__ == '__main__':
    app.run(debug=True)


