import json

from pprint import pprint

def create_index(es, index_name):
    created = False
    # index settings
    settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "contact": {
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


def get_id(es, param_dict, index_name):

    query_list = []

    for key, value in param_dict.items():
        if param_dict[key]:
            query_list.append({"term": {key : value}})

    
    res = es.search(index=index_name, body={"query": {"bool": {"should": query_list}}})
    if res['hits']['total'] > 0:
        _id  = res['hits']['hits'][0]['_id']
        name = res['hits']['hits'][0]['_source']['name']
        return _id, name
    else:
        return False, False


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
        elif key == 'address':
            body[key] = body[key].lower().replace(' ','')
            if body[key].isalnum() == False:
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



# Populate db with mock data

def populate_index(path, es, index_name):
    counter = 0
    with open(path) as f:
        data = json.load(f)

        for i in data:
            i = body_cleaner(i)
            name = {'name': i['name']}
            counter += 1

            name_id, name = get_id(es, name, index_name)
            if name_id == False:
                try:
                    post_outcome = es.index(index=index_name, doc_type='contact', body=i)
                except Exception as ex:
                    print('Error in indexing data')
                    print(str(ex))

    


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