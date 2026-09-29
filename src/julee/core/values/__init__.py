"""What the kernel is made of but does not keep.

A value object has no identity, so no repository keeps one and no port
can be bound to one (ADR 018). Fourteen of the kernel's classes are
values, and they were counted as entities because they sat beside them:
a port naming a ``ClassInfo`` or a ``PolicyVerificationResult`` read as
a port bound to an aggregate.

julee has no bounded context, so this is the kernel's ``domain/values/``.

Import from the submodule, not from here.
"""
