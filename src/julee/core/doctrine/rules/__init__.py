"""Doctrine rules as plain functions, so they can be tested.

A rule decides whether a codebase is acceptable, which makes it code
worth being sure about. Here each one is a function over data returning
what it objects to; the pytest rule beside it fetches the data, calls
this, and asserts. That way a rule can be shown to fire without pointing
it at a real codebase and breaking something.
"""
