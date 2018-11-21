# Address-book-api
Take home interview challenge: Create an API using Elasticsearch


 ## API DOCs:
  

**GET**:

    Full query:
        No pagination:
            /contact
        Pagination:
            /contact?page={int}&pageSize={int}

    Partial query:
        /contact?name={ txt }&phone={ num }&address={ num+txt }&city={ txt }&state={ txt }&zip={ num }

**POST**:

    /contact
        + Body

**PUT**:

    /contact?name={ txt }&phone={ num }&address={ num+txt }&city={ txt }&state={ txt }&zip={ num } 
        + Body

**DELETE**

    /contact?name={ txt }&phone={ num }&address={ num+txt }&city={ txt }&state={ txt }&zip={ num } 

---

 - When querying by URL, only one parameter is needed.  In fact, all "name"s are unique, so you don't need anything else.
If you need to use something other than a "name" it is recommended that you use multiple parameters, as "name" is the only
parameter guaranteed to be unique.


 - The required body layout for POST and PUT looks like this:



  ```
  {

    "name": {str},
    "phone": {10 digit num},
    "address": {str},
    "city": {str},
    "state": {str},
    "zip": {<10 digit num}

  }
  ```

  for example:
  ```
  {

    "name": "Bradley Chapman",
    "phone": 5461768427,
    "address": "574 Lancaster Avenue",
    "city": "Bancroft",
    "state": "Nevada",
    "zip": 7036

  }
  ```