# Import dependencies
from datetime import datetime
from elasticsearch import Elasticsearch

from flask import Flask, render_template, redirect, request, jsonify
from flask_restful import Resource, Api

from pprint import pprint

import json

from modules.index_builder import create_index, get_id, body_cleaner, populate_index

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

# def body_cleaner(body):

#     formatting = True

#     keys_to_be_deleted = []

#     for key, value in body.items():
#         if body[key] is None:
#             keys_to_be_deleted.append(key)
#             continue
#         elif key == 'phone':
#             body[key] = str(body[key])
#             if len(body['phone']) != 10:
#                 formatting = False
#         elif key == 'zip':
#             body[key] = str(body[key])
#             if len(body['zip'])   >  10:
#                 formatting = False
#         elif key == 'address':
#             body[key] = body[key].lower().replace(' ','')
#             if body[key].isalnum() == False:
#                 formatting = False
#         else:
#             body[key] = body[key].lower().replace(' ', '')
#             if body[key].isalpha() == False:
#                 formatting = False

#     for key in keys_to_be_deleted:
#         del body[key]

#     if formatting == False:
#         pprint(body)
#         return 'Input was formatted incorrectly'

#     else:
#         return body
    



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
    


# def get_id(name):
#     res = es.search(index=index_name, body={"query": {"term": {"name": name}}})
#     if res['hits']['total'] > 0:
#         return res['hits']['hits'][0]['_id']
#     else:
#         return False

# def query_handler(get_query):
#     res = es.search(index=index_name, body=get_query)
#     return res

# def post_name(doc):

#     name = doc['name']
#     phone = doc['phone']
#     address = doc['address']
#     city = doc['city']
#     state = doc['state']
#     _zip = doc['zip']

#     name = name.lower().replace(" ", "")
#     address = address.lower().replace(" ", "")
#     city = city.lower().replace(" ", "")
#     state = state.lower().replace(" ", "")
#     phone = str(phone)
#     _zip = str(_zip)

#     if (
#         name.isalpha()  == False or
#         len(phone)      != 10    or
#         city.isalpha()  == False or
#         state.isalpha() == False or
#         len(_zip)       >  10
#     ):
#         return "Input improperly formatted"

#     else:
#         doc['name'] = name
#         doc['phone'] = phone
#         doc['address'] = address
#         doc['city'] = city
#         doc['state'] = state
#         doc['zip'] = _zip



#     name_id = get_id(doc['name'])
#     if name_id == False:
#         try:
#             post_outcome = es.index(index=index_name, doc_type='contacts', body=doc)
#             return True, post_outcome
#         except Exception as ex:
#             print('Error in indexing data')
#             print(str(ex))
#             return False, f'Something went wrong, exception thrown'
#     else:
#         return False, 'Name unavailable'

# def get_name(name):
#     res = es.search(index=index_name, body={"query": {"match": {"name": f"{name}"}}})
#     return res

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

@app.route('/restart_index')
def restart():
    es.indices.delete(index_name)
    create_index(es, index_name)
    populate_index('resources/generated.json', es, index_name)

    return 'Index populated'


@app.route('/contacts',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def contacts():

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
    except:
        print('No JSON body included')

    # query     = request.args.get('query') I don't understand how to get this to work.
    page_size = request.args.get('pageSize')
    page      = request.args.get('page') 


    if page_size:
        try:
            page_size = int(page_size)
        except Exception as ex:
            print('page and page_size must be integers')
            return 'page and page_size must be integers'
    else:
        page_size = 50

    if page:
        try:
            page = int(page)
        except Exception as ex:
            print('page and page_size must be integers')
            return 'page and page_size must be integers'
    else:
        page = 1

    if request.method == 'GET' and len(param_dict.items()) == 0:

        match_all_doc = {
                'size' : 10000,
                'query': {
                    'match_all' : {}
                }
            }
        res = es.search(index=index_name, doc_type='contacts', body=match_all_doc)

        print(page)

        first_doc = page_size * (page - 1)
        last_doc  = page_size * page

        return jsonify(res['hits']['hits'][first_doc:last_doc])
        # return jsonify(res)


    elif request.method == 'GET':
        query_list = []

        for key, value in param_dict.items():
            if param_dict[key]:
                query_list.append({"term": {key : value}})

        res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})
        pprint(res)
        return jsonify(res)

    elif request.method == 'POST' and body:
        pprint(body)
        name_id = get_id(es, body['name'], index_name)
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
        if body and param_dict['name']:
            name = param_dict['name']
            name_id = get_id(es, name, index_name)
            print('made it here')
            if name_id:
                try:
                    res = es.update(index=index_name, doc_type='contacts', id=name_id, body={"doc": body})
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
        if param_dict['name']:
            name = param_dict['name']
            name_id = get_id(es, name, index_name)
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




if __name__ == '__main__':
    app.run(debug=True)


