This project repository assumes that you are use pre-commit
in a python virtualenv, where requirements.txt are pip installed.
That will also install aider, which you may or may not want to use.

So do something like this and you should be good to go:

```bash
virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

Note CONVENTIONS.md is for both your and aider's benefit.

See docs/ for guidance on software development lifecycle, etc.
In a nutshell, this project/repository is for coordination,
all the real coding happens in the reference implementation repos.
