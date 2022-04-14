# GistHub
Retrieve Github gists for specific users using different filters

## Install the required dependencies
```
pip install -r requirements.txt
```

## General usage
```
python gisthub.py --help
```
```
usage: gisthub.py [-h] user, gist, search ...

optional arguments:
  -h, --help          show this help message and exit

subcommands:
  The available subcommands are listed below.

  user, gist, search

```
## Perform user-related operations
```
python gisthub.py user --help
```

```
usage: gisthub.py user [-h] [--username USERNAME] [--username-list USERNAMES_FILE] [--maximum INTEGER] [--save FILE] [--save-id FILE] [--save-metadata FILE] [--verbose]

This subcommands performs user-related activities.

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME, -u USERNAME
                        specify the username of the users whose gists should be retrieved. Repeat the flag to add multiple usernames.
  --username-list USERNAMES_FILE, -L USERNAMES_FILE
                        specify the file containing usernames.
  --maximum INTEGER, -m INTEGER
                        specify the maximum number of gists to retrieve. Default is 100.
  --save FILE, -s FILE  specify the file to save the retrieved gists. Format is JSON.
  --save-id FILE        specify the file(flat) to save the ids(s) only. Format is TXT
  --save-metadata FILE, -S FILE
                        specify the file to save the metadata of the gists. Format is JSON
  --verbose, -v         specify the verbosity of the program.
```


## Perform gist-related operations
```
python gisthub.py gist --help
```

```
usage: gisthub.py gist [-h] [--gists GIST_ID] [--gist-list GISTS_FILE] [--maximum INTEGER] [--save FILE] [--save-metadata FILE] [--verbose]

This subcommands performs gist-related activities.

optional arguments:
  -h, --help            show this help message and exit
  --gists GIST_ID, -g GIST_ID
                        specify the gist ids of the gist that should be retrieved. Repeat the flag to add multiple ids.
  --gist-list GISTS_FILE, -L GISTS_FILE
                        specify the file containing gist ids.
  --maximum INTEGER, -m INTEGER
                        specify the maximum number of gists to retrieve. Default is 0(which means all gists in the user's timeline).
  --save FILE, -s FILE  specify the file to save the retrieved gists. Format is JSON.
  --save-metadata FILE  specify the file to save the metadata. Format is JSON
  --verbose, -v         specify the verbosity of the program.
```

## Perform search-related operations
```
python gisthub.py search --help
```

```
usage: gisthub.py search [-h] --query QUERY [--language LANGUAGE] [--page INTEGER] [--max-gists INTEGER] [--max-pages INTEGER] [--sort SORT] [--order ORDER] [--get-all]
                         [--save FILE] [--save-usernames FILE] [--save-metadata FILE] [--verbose]

This subcommands performs search-related activities.

optional arguments:
  -h, --help            show this help message and exit
  --query QUERY, -q QUERY
                        specify the query.
  --language LANGUAGE, -l LANGUAGE
                        specify the language of the gists to return. Values include Markdown,CSV,HTML,JavaScript,JSON,XML,Python,SCSS,Shell,Text.
  --page INTEGER, -p INTEGER
                        specify the page to start from. Default is 1.
  --max-gists INTEGER, -m INTEGER
                        specify the maximum number of gists to retrieve. Default is 100.
  --max-pages INTEGER, -M INTEGER
                        specify the maximum number of pages to retrieve. Default is 100.
  --sort SORT, -x SORT  specify the way to sort the result.
  --order ORDER, -o ORDER
                        specify the order of the sort.
  --get-all, -G         specify that the maximum possible number of gists should be retrieved.
  --save FILE, -s FILE  specify the file to save the retrieved gists. Format is JSON.
  --save-usernames FILE
                        specify the file(flat) to save the usernames of users who authored the gists. Format is TXT.
  --save-metadata FILE, -S FILE
                        specify the file to save the metadata. Format is JSON.
  --verbose, -v         specify the verbosity of the program.
```
