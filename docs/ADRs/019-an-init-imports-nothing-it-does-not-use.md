# ADR 019: An `__init__.py` Imports Nothing It Does Not Use

## Status

Accepted

## Date

2026-09-30

## Context

ADR 001 §5 said each package's `__init__.py` exports its public API,
and gave `from julee.contrib.ceap import ExtractAssembleDataUseCase` as
the way a solution reaches a kit. `julee.contrib` no longer exists; the
kits ship as their own wheels, and what that section described has
become 48 `__init__.py` files across julee and the kits that import
names from the modules beside them and list them in `__all__`. 170
imports in the estate go through one.

A re-export buys nothing a direct import does not. It costs a layer of
indirection between a name and where it lives, and it costs more than
that:

- **A habit has been shaping a rule.** The rule that a use case may not
  import another use case (#321) should be one line: `usecases` is not
  among the packages a use case may import from. The rule that shipped
  is narrower — only a module that *defines* a `*UseCase` is held to it
  — and the sole reason for the narrowing is that `usecases/__init__.py`
  imports every use case beside it in order to re-export them, and
  would otherwise be the first offender. `rules/dependency.py` says so
  in its own words: "a concession to re-exports rather than something
  the rule wants".

- **A facade outlives its callers without anyone deciding.**
  `julee_hcd/usecases/__init__.py` re-exports twenty-two names. After
  four PRs moved the calculations they named into the domain, nothing
  imports any of them, and the file did not change, because nothing
  about a facade says when it is done.

- **A facade hides where a thing lives.** `from julee_hcd.usecases import
  get_epics_for_story` said the function was a use case. It was a pure
  function over entities, and the directory it was really in was the
  clue that it was misfiled. Three such files were removed this week
  (julee-kits #119, #121); the facade had made them look like API.

- **ruff cannot see through `__all__`.** F401 reports an unused import
  everywhere except where `__all__` names it, so the one tool that
  would have counted these files was told not to.

### What "re-export" means

A name is re-exported when `__init__.py` imports it and does nothing
with it but list it in `__all__`. That is the whole test, and it is the
right test because it says what the file is for rather than what it
contains:

- `julee/core/entities/__init__.py` imports `dataclasses`, `pkgutil`
  and `BaseModel` and uses all three in `kernel_entity_names()`. Not a
  re-export. It is a module that happens to be an `__init__`.
- A Sphinx extension's `__init__.py` imports its directives and
  registers them in `setup(app)`. Not a re-export. Registering is using.
- `julee/repositories/memory/__init__.py` imports `MemoryRepositoryMixin`
  from `.base` and lists it in `__all__`. A re-export, and eighteen
  files import it from the wrong place.

So there is no list of exceptions to maintain. A module that uses what
it imports is a module; one that only passes it on is a facade.

## Decision

**An `__init__.py` imports nothing it does not use.** A name is
imported from the module that defines it. `from x import *` is a
re-export of everything and is refused outright.

ADR 001 §5 is reversed.

Doctrine reads every `__init__.py` under the target's `search_root`
and objects to each imported name that appears nowhere in the module
but `__all__`. It walks the search root rather than the bounded
contexts, because a facade is a property of a package, not of a
context — and because julee itself has no bounded contexts and would
otherwise be exempt from a rule about its own files.

### Consequences

- 48 files lose their imports and `__all__`, keeping their docstrings.
  170 import sites are repointed to the defining module, mechanically:
  each name is looked up in the facade and imported from wherever
  `__module__` says it was defined, which is how the CRUD generator
  now resolves a request's types (julee #349). mypy names every site
  a script misses.
- The rule lands before the sweep, not after. A kit's doctrine is red
  until its facades are gone, and the count is the worklist. That is
  how ADR 018's directory rule took ceap from three objections to zero.
- Once no `usecases/__init__.py` imports a use case, #321's rule
  collapses to the line it wanted: `usecases` leaves
  `USE_CASE_PACKAGES`, and the "defines a `*UseCase`" narrowing and its
  filter are deleted.
- Removing a facade is a public-API removal for anything that imported
  through it. Each affected kit takes a version bump, per #322.
- Where a package's docstring used to say "import from the submodules",
  it now says nothing, because there is no other way.
