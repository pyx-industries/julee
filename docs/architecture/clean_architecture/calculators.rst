Calculators
===========

**Calculators work out an answer from what you hand them.**

Same arguments, same answer, every time.
A calculator does no I/O and holds no state.

::

    class NewDataCalculator(Protocol):
        async def identify_new_items(
            self, previous_data: bytes | None, new_data: bytes
        ) -> list[str]: ...

Calculators are defined as :doc:`protocols`;
the :doc:`DI container <dependency_injection>` provides implementations.

A calculator may be bound to any number of :doc:`entities`—none, one,
or several. What makes it a calculator is that its answer follows from
its arguments, not how many entities those arguments involve.

Calculators Run Inline
----------------------

A :doc:`pipeline </architecture/solutions/pipelines>` calls a calculator
directly, in workflow code, without an activity.
Replaying the workflow re-runs the calculation and gets the same answer,
which is all Temporal needs.

This is the point of naming them.
Without the word, the reflex is to wrap everything in an activity
and pay a round trip and a serialisation hop
to compare two byte strings.

Why Not A Method On The Entity?
-------------------------------

:doc:`Entities <entities>` are rich objects that validate and calculate properties,
so a calculation that concerns one entity
could perfectly well be a method on it.
Often it should be.

The test is who the answer belongs to.

**An intrinsic rule with one right answer is a method on the entity.**
Whether a date falls inside a range, whether required fields agree,
how a total is derived from its parts—the concept carries these
wherever it goes.

**A rule that varies by adopter is a calculator.**
A kit ships ``Story``; the solution that adopts it
decides what "important" means.
The entity cannot carry every adopter's version of that rule,
and should not import what it would need to.

That makes a calculator the seam a kit uses
to require something of its adopter—:doc:`ADR 012
</ADRs/012-framework-and-kits>`'s contribution contract
running the other way. The kit declares the protocol
and never implements it; the solution supplies the answer.
