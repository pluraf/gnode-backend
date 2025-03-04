# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* Setup venv and install requirements
```

    python -m venv venv

    source venv/bin/activate

    pip install -r requirements.txt

```

* set db parameters in dev.env file and export them using env.sh

```

    source env.sh
```

* start fastapi application
```

    uvicorn app.main:app --reload --port 8888
```

---

Before commit run "black ./app"

---
To install psycopg2 first install:
```
sudo apt-get install libpq-dev
```

---

To try out APIs, start fastapi application and navigate to
http://localhost:8888/api/docs


### How do I run tests? ###
* Setup venv and install requirements

```

    python -m venv venv

    source venv/bin/activate

    pip install -r requirements.txt

    pip install -r requirements-dev.txt


```

* Set environment variables 

```
    source env.sh

```

NOTE: The DB environment variables are changed when running tests. can be found in set_test_env_vars() function in conftest.py They are automatically changed back after test session ends.

* Run pytest

```
    pytest
```

To run specific test file:

    pytest <test_file_path>

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
