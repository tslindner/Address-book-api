# Import dependencies
from datetime import datetime
from elasticsearch import Elasticsearch

from flask import Flask, render_template, redirect, request, jsonify
from flask_restful import Resource, Api

from pprint import pprint

import json

# create_index initializes the index when passed an elasticsearch conn and an index name
# get_id checks for and returns an id and name when given search paremeters.  If the check fails it returns False
# body_cleaner formats input so that elasticsearch won't get mad about it anymore. It's passed and returns a dict
# populate_index fills the index with a premade JSON address book found under resource/generated.json.  It's passed a path, ES conn, and index name.
from modules.index_builder import create_index, get_id, body_cleaner, populate_index

# connect to ES

# port = input('What port would you like to connect to?')

port = 9200
es = Elasticsearch(HOST='http://localhost', PORT=port)
index_name = 'address_book'

# init ES index
es.indices.delete(index_name)
create_index(es, index_name)
populate_index('resources/generated.json', es, index_name)


# init flask
app = Flask(__name__)
api = Api(app)

# Access to a fresh index for testing purposes
@app.route('/restart_index')
def restart():
    es.indices.delete(index_name)
    create_index(es, index_name)
    populate_index('resources/generated.json', es, index_name)

    return 'Index populated'

# Main endpoint handler
@app.route('/contact',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def contact():

    # Collect search parameters in a dict and clean them
    param_dict =    body_cleaner(dict(  
                    name      = request.args.get('name'),
                    phone     = request.args.get('phone'),
                    address   = request.args.get('address'),
                    city      = request.args.get('city'),
                    state     = request.args.get('state'),
                    zip       = request.args.get('zip')))

    # body_cleaner will return a string if no parameters are passed
    if isinstance(param_dict, str):
        return param_dict

    # A JSONEncoder error is thrown when the body of the request is empty
    try:
        body = body_cleaner(request.get_json())
    except Exception as ex:
        body = None
        print('No JSON body included')
        print(str(ex))


    # query     = request.args.get('query') I don't understand how to get this to work.
    page_size = request.args.get('pageSize')
    page      = request.args.get('page') 


    # page and page_size are collected as strings and need to be converted to int
    # if they are not passed, default values are given that coincide with the max allowed by ES
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

    # GET without parameters -----------------------
    # Input:  None. However, the URL parameters must be empty
    # Action: Queries ES for all records
    # Output: All records in JSON format, limited by page/page_size or the ES limit of 10,000
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


    # GET specified by parameters -------------------
    # Input:  URL parameters
    # Action: Queries ES for matching records 
    # Output: Matching records in JSON format
    elif request.method == 'GET':
        query_list = []

        for key, value in param_dict.items():
            if param_dict[key]:
                query_list.append({"term": {key : value}})

        res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})
        res = [doc['_source'] for doc in res['hits']['hits'] if isinstance(res['hits']['hits'], list)]
        return jsonify(res)


    # POST  -----------------------------------------
    # Input:  Body
    # Action: Creates new record using data from body
    # Output: Messages in str form
    elif request.method == 'POST':
        if body is not None:
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

    # PUT ------------------------------------------
    # Input:  Body and URL parameters
    # Action: Updates record found by URL parameter query, using new data from body
    # Output: Messages in str form
    elif request.method == 'PUT':
        if body and len(param_dict.items()) != 0:
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

    # DELETE ---------------------------------------
    # Input:  URL parameters
    # Action: Deletes a record
    # Output: Messages in str form
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


