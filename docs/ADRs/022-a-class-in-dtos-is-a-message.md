# ADR 022: A Class in `dtos/` Is a Message

## Status

Draft

## Date

2026-10-02

## Context

ADR 001 gave a bounded context one place for pydantic, `dtos/`, and said
what goes there: the messages at the driving port, which are pydantic
models. Doctrine enforced that for part of the directory.

The class parser did not read `dtos/`. A class there reached doctrine
only if its name ended in `Request` or `Response` and a use case file
imported it; the parser then knew the name, and a rule resolved it and
asked whether it was a pydantic model. Everything else in the directory
was read by nothing.

Run against a solution with one use case, `julee doctrine verify` gave
these results before this ADR:

| Solution | Doctrine |
|----------|----------|
| The request a use case takes is not a pydantic model | Objects |
| A request no use case imports is not a pydantic model | Passes |
| A class in `dtos/` named neither Request nor Response is not a pydantic model | Passes |

The second is a message half written, which is when it would be useful
to be told. The third is most of what `dtos/` holds besides requests and
responses: the nested messages a response is built from. `julee-c4`,
`julee-ceap` and `julee-hcd` have seventeen of them between them.

This is the arrangement ADR 002 warns about and ADR 020 removed for use
cases: a name, and here an import as well, deciding what doctrine reads.

## Decision

**A class in `dtos/` is a message.** Doctrine finds it by where it sits,
and holds it to the rule ADR 001 states: a class in `dtos/` is a
pydantic model.

One other kind of class may live there: **an enum.** An enum that types
a field of a message is part of what the message says. It is a closed
set of values with an obvious serialised form, and one that exists for a
message has no better home. The rule does not ask whether a message
uses it.

A pydantic dataclass is refused in `dtos/` as it already is for a
request or a response: it reads as a plain dataclass everywhere else
and so belongs to neither ring.

The class is judged by importing its module and asking Python, as a
request is, because a base called `BaseModel` in the source is not
proof of pydantic's.

## Consequences

- The parser has a `dtos` family: every class in `dtos/`.

- A request or a response in `dtos/` is in that family as the class it
  is. It is still in `requests` or `responses` as the name a use case
  knows it by, and the rules that match a use case to its messages are
  unchanged.

- A class in `dtos/` that is neither a pydantic model nor an enum is
  objected to, whether or not anything imports it and whatever it is
  called.

- Every class in the kits' `dtos/` is a pydantic model, so the kits pass
  as they are.

- `julee doctrine census` reports a class in `dtos/` as claimed at its
  location by the `dtos` family. `claimed by name` and `candidate` are
  left for a message declared somewhere no family reads.

### What this does not reach

How a use case is matched to its request and response. That is still by
name, through what the use case file imports, which is why the names
must be unambiguous. Finding a message by its declaration in `dtos/`
instead would give it a location and is a larger change than this one.

A function in `dtos/`. No family holds a function.

## Relationship to earlier ADRs

- **ADR 001** said pydantic lives in `dtos/` and that a message is a
  pydantic model. This makes doctrine read the directory it spoke of.
- **ADR 002** is applied: `dtos/` is read by directory, as services,
  handlers and use cases are.
- **ADR 020** did the same for `usecases/`, and left a class named as a
  request or response to be a message. This says what a message must
  be.
