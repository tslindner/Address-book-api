import json
import requests
import unittest

from pprint import pprint

from modules.index_builder import body_cleaner

base_url = 'http://localhost:5000/'

with open('resources/generated.json') as f:
    answer_data = json.load(f)

answer_data = [body_cleaner(doc) for doc in answer_data]


class TestGetMethods(unittest.TestCase):

    # All tests are run with a freshly restarted mock dataset
    def setUp(self):
        requests.get(f'{base_url}restart_index')

    # full query
    def test_full_index(self):
        test_data = requests.get(f'{base_url}contact').json()
        self.assertEqual(len(test_data), len(answer_data))

    # page/pageSize
    def test_with_pages(self):
        test_data = requests.get(f'{base_url}contact?page=3&pageSize=15').json()
        self.assertEqual(test_data, answer_data[30:45])

    # single URL parameter: name
    def test_with_name(self):
        test_data = requests.get(f'{base_url}contact?name=TraCey mAsOn').json()
        self.assertEqual(test_data[0], answer_data[0])

    # single URL parameter: phone
    def test_with_phone(self):
        test_data = requests.get(f'{base_url}contact?phone=5461768427').json()
        self.assertEqual(test_data[0], answer_data[1])

    # single URL parameter: address
    def test_with_address(self):
        test_data = requests.get(f'{base_url}contact?address=956 ArkAn sasDrive').json()
        self.assertEqual(test_data[0], answer_data[2])

    # multi URL parameter: city, state, zip
    def test_with_citystatezip(self):
        test_data = requests.get(f'{base_url}contact?city=Chautauqua&state=RhOdeIs laNd&zip=2544').json()
        self.assertEqual(test_data[0], answer_data[3])

    # failstate: parameter (name) matches no records
    def test_get_fail(self):
        test_data = requests.get(f'{base_url}contact?name=tim lindner').json()
        self.assertEqual(test_data, [])


class TestPostMethods(unittest.TestCase):

    # All tests are run with a freshly restarted mock dataset
    def setUp(self):
        requests.get(f'{base_url}restart_index')

    # single POST request
    def test_single_post(self):
        new_contact =   body_cleaner({
                                    "name": "Tim Lindner",
                                    "phone": 2769674444,
                                    "address": "508 Pershing Loop",
                                    "city": "Dunbar",
                                    "state": "New Jersey",
                                    "zip": 7051
                                    })

        test_single_post = requests.post(f'{base_url}contact', json=new_contact)
        check_single_post = requests.get(f'{base_url}contact?name=tim lindner').json()
        self.assertEqual(check_single_post[0]['phone'], new_contact['phone'])

    # failstate: duplicate POST requests
    def test_double_post(self):
        new_contact =   body_cleaner({
                                    "name": "Tim Lindner",
                                    "phone": 2769674444,
                                    "address": "508 Pershing Loop",
                                    "city": "Dunbar",
                                    "state": "New Jersey",
                                    "zip": 7051
                                    })

        test_double_post_1 = requests.post(f'{base_url}contact', json=new_contact)
        test_double_post_2 = requests.post(f'{base_url}contact', json=new_contact)
        self.assertEqual(test_double_post_2.text[0:17], 'Name unavailable.')

    # failstate: empty body in POST request
    def test_empty_post(self):
        test_empty_post = requests.post(f'{base_url}contact')
        self.assertEqual(test_empty_post.text, 'No JSON body included')


class TestPutMethods(unittest.TestCase):

    # All tests are run with a freshly restarted mock dataset
    def setUp(self):
        requests.get(f'{base_url}restart_index')

    # single PUT request
    def test_single_put(self):
        updated_contact =   body_cleaner({
                                    "name": "Tim Lindner",
                                    "phone": 2769674444,
                                    "address": "574 Lancaster Avenue",
                                    "city": "Avalon",
                                    "state": "Rhode Island",
                                    "zip": 6944
                                    })

        test_single_put = requests.put(f'{base_url}contact?name=bradley chapman', json=updated_contact)
        test_single_put_result = requests.get(f'{base_url}contact?name=tim lindner').json()
        self.assertEqual(test_single_put_result[0]['address'], updated_contact['address'])

    # failstate: missing URL parameters in PUT request
    def test_put_missing_params(self):
        updated_contact =   body_cleaner({
                                    "name": "Tim Lindner",
                                    "phone": 2769674444,
                                    "address": "574 Lancaster Avenue",
                                    "city": "Avalon",
                                    "state": "New Jersey",
                                    "zip": 6944
                                    })

        test_put = requests.put(f'{base_url}contact', json=updated_contact)
        self.assertEqual(test_put.text[0:68], 'You must pass a name and an updated document when passing a PUT call')

    # failstate: empty body in PUT request
    def test_put_missing_body(self):
        test_put = requests.put(f'{base_url}contact?name=bradley chapman')
        self.assertEqual(test_put.text, 'You must pass a name and an updated document when passing a PUT call. PUT aborted')



class TestDeleteMethods(unittest.TestCase):

    # All tests are run with a freshly restarted mock dataset
    def setUp(self):
        requests.get(f'{base_url}restart_index')

    # single DELETE request
    def test_delete(self):
        test_delete = requests.delete(f'{base_url}contact?name=tracey mason')
        self.assertEqual(test_delete.text[0:20], 'Successfully deleted')

    # failstate: no matching entry for URL parameters
    def test_delete_fail(self):
        test_delete_fail = requests.delete(f'{base_url}contact?name=tim lindner')
        self.assertEqual(test_delete_fail.text[0:44], 'No entry by that name exists. DELETE aborted')


if __name__ == '__main__':
    unittest.main()