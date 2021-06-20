# RRBot

TODO:
Instructions for use

## Setup checklist

* mysql-client
  MacOS: `brew install mysql-client`
* python requirements
  `py3 -m pip install -r requirements.txt`
* docker (optional)
  `docker compose up -d`


## Contributing

1. fork this repository
2. clone it down to your local dev machine
3. run `python3 -m pip install -r requirements.txt` to get your packages
4. run `cp src/configuration.py.sample src/configuration.py` and edit the new file to ensure your database URL is correct if you are not using docker.
5. develop features in a features/<feature-name> branch
6. include tests where possible
7. when you are finished, be sure to rebase your master then rebase the feature to master
8. push back to your repository
9. create a pull request for review
