Protocols
=========

**Protocols define interfaces.**

Python Protocols are key to how Julee interfaces with infrastructure.

:doc:`Repositories <repositories>` and :doc:`services` are both defined as Python Protocols.
We use modern python typing to ensure infrastructure components
(actual repository and service implementations)
implement those interfaces, and this is relied upon by :doc:`use cases <use_cases>`
and leveraged by :doc:`dependency injection <dependency_injection>`.
This is why :doc:`applications </architecture/applications/index>` don't need to think about it,
they just run the use cases.

The service and repository interfaces are typed such that
they only deal in :doc:`entities` and simple primitives.
