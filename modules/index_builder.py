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


def get_id(es, name, index_name):
    res = es.search(index=index_name, body={"query": {"term": {"name": name}}})
    if res['hits']['total'] > 0:
        return res['hits']['hits'][0]['_id']
    else:
        return False


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
    with open(path) as f:
        data = json.load(f)

        for i in data:
            i = body_cleaner(i)

            name_id = get_id(es, i['name'], index_name)
            if name_id == False:
                try:
                    post_outcome = es.index(index=index_name, doc_type='contacts', body=i)
                except Exception as ex:
                    print('Error in indexing data')
                    print(str(ex))
                    return False, f'Something went wrong, exception thrown'
            else:
                return False, 'Name unavailable'


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