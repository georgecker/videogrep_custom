# What this is
This is a custom version of the videogrep tool by Sam Lavigne. The only difference is that mine does support the search type 'ordered' which allows you to create a super cut with a single use of the provided phrase and its order.

[The original repo](https://github.com/antiboredom/videogrep)

## How to
### Make sure you have python3 installed
### This guide is only for UNIX like operating systems

1. Download repo
2. Open repo in terminal
3. Create virtual environment
   `python3 -m venv ./venv`
4. Source shell
   `source ./venv/bin/active`
5. Navigate to src dir and install dependancies
   `python3 -m pip install -r requirements.txt`
6. Run it. See flags with -h flag
   `python3 __main__.py -h`
