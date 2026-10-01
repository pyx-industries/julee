# ADR 020: A Class in `usecases/` Is a Use Case

## Status

Draft

## Date

2026-10-02

## Context

ADR 002 says doctrine finds an artifact by the directory it sits in and
then checks what it calls itself, and gives the reason: a name used to
find things is a filter, and a filter that misses something drops it
without saying so. Services were moved to that footing after #175 and
handlers after #256.

Use cases were not. The parser read every class under `usecases/` and
kept the ones whose names end in `UseCase`. That was the definition of a
use case, and three things followed from it.

- **The naming rule had nothing to object to.**
  `test_all_use_cases_MUST_end_with_UseCase` ran over a list that had
  already been filtered by that suffix, so its list of offenders was
  always empty. It could fail only through its canary, when no use case
  was found at all.

- **No other rule could fail on a misnamed class either.** A class in
  `usecases/` called anything else was in no family, so nothing asked
  whether it had a docstring, an `execute()`, a request or a response.
  The rules already expect to meet such a class:
  `use_cases_without_request` skips a badly named one, and its test says
  that one is left to the naming rule. The naming rule never saw it.

- **Nothing said what else was in the directory.** `julee doctrine census`
  lists the classes no family holds, and in `julee_hcd` it listed
  `SuggestionRepositories`, a dataclass in `usecases/suggestions.py`
  that no other file in the kits names. Doctrine had passed over it for
  as long as it had been there.

### What a definition has to do

Three things are wanted of doctrine here: a definition of what is and is
not a use case, rules about what must be true of one, and an objection
to whatever is use-case-ish and not a valid use case.

The old definition did the first by borrowing one of the rules, which
left that rule with nothing to do and made the third impossible. A thing
that fails the definition is invisible, and nothing objects to what it
cannot see.

So the definition has to be wider than validity. It says what doctrine
looks at. The rules say what that must satisfy. The objection to an
impostor is then what the rules were always for.

## Decision

**A class in `usecases/` is a use case.** Doctrine finds it by where it
sits. What it is called, and whether it can be executed, are rules.

The one exception is a message. A class in `usecases/` whose name ends
in `Request` or `Response` is a request or a response, as it was.

Declaring `execute()` is not part of the definition, though it would
pick out the same classes in every kit today. If it were, the rule that
a use case can be executed would be the one with nothing to object to.

The rules are unchanged in what they say. A use case's name ends in
`UseCase`, it says what it does, it can be executed, and it takes its
own request and returns its own response. What changes is that each of
them now meets every class in the directory.

### Nothing else lives in `usecases/`

A helper, a shared base class, a port and an exception are each a class
in `usecases/` that is not a use case, and each is now objected to: by
the naming rule, and by the `execute()` rule unless it inherits one.
The answer is to move it, or to make it the use case it was sitting
among.

This is not a new restriction so much as the other half of two that
exist. A use case may not import from a `usecases` package, its own or
another's (ADR 019 removed the last exception), so a helper there has no
caller that is allowed to reach it. And a port belongs under `domain/`
(ADR 016). A class in `usecases/` that is not a use case was already
somewhere it could not be used from.

### The name is still doctrine

A solution cannot declare that its use cases are called something else.
ADR 005 makes doctrine axiomatic, and what a use case is called is part
of what makes it one to a reader, to the CRUD generator and to the
pipeline parser, all of which go by the suffix.

## Consequences

- The use case family is every class the parser reads under `usecases/`
  that is not a request or a response. In `julee-c4`, `julee-ceap` and
  `julee-polling` that is the family they had. In `julee-hcd` it is the
  41 it had and `SuggestionRepositories`, which the naming rule and the
  `execute()` rule now object to. It is removed in the kits.

- `test_all_use_cases_MUST_end_with_UseCase` can find an offender, and a
  test in `doctrine_suite/` runs it against a solution where it must.

- A solution that kept helpers in `usecases/` sees an objection for each
  the first time it runs this. That is the survey ADR 002 describes, and
  there is no way to silence it one class at a time.

- `julee doctrine census` reports a class in `usecases/` as claimed by
  the use case family whatever it is called. Claimed still means a
  member of a family, not compliant.

- `GENERIC_BASE_CLASSES` is as it was: a named base that exists to be
  subclassed needs no request or response of its own.

### What this does not reach

The parser skips a module whose name begins with an underscore and a
class whose name begins `Test`, in `usecases/` as everywhere. A class in
either place is still not read. Both are name filters of the kind this
ADR removes one of, and both are left for their own decisions.

A function in `usecases/` is in no family. No family holds a function.

## Relationship to earlier ADRs

- **ADR 002** is applied, not amended: use cases join services and
  handlers under Discovery by Directory, Naming by Rule, and a paragraph
  there now says so.
- **ADR 005** is why the suffix remains a rule for every solution.
- **ADR 014** named the package. This says what is in it.
- **ADR 019** made `usecases` a package no use case imports from, which
  is what leaves a helper there with no caller.
