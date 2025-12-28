{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}
   :members:
   :undoc-members:
   :show-inheritance:

{% if modules %}
.. rubric:: Submodules

.. autosummary::
   :toctree:
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}

{% if "solution" in fullname and "entities" in fullname %}
This Solution
-------------

.. solution-overview::

Bounded Contexts
~~~~~~~~~~~~~~~~

.. bounded-context-list::
   :show-description:

Applications
~~~~~~~~~~~~

.. application-list::
   :show-description:

Deployments
~~~~~~~~~~~

.. deployment-list::

Viewpoints
~~~~~~~~~~

.. viewpoint-links::

Nested Solutions
~~~~~~~~~~~~~~~~

.. nested-solution-list::

{% elif fullname.startswith("julee.") and fullname.count(".") == 1 and fullname.split(".")[-1] not in ["contrib"] %}
{# This is a BC module page like julee.hcd, julee.core, julee.c4 #}
{% set bc_slug = fullname.split(".")[-1] %}

BC Contents
-----------

.. bc-hub:: {{ bc_slug }}

{% elif "bounded_context" in fullname %}
This Solution's Bounded Contexts
--------------------------------

.. bounded-context-list::
   :show-description:

{% elif "application" in fullname and "entities" in fullname %}
This Solution's Applications
----------------------------

.. application-list::
   :show-description:

{% elif "deployment" in fullname and "entities" in fullname %}
This Solution's Deployments
---------------------------

.. deployment-list::

{% elif "entity" in fullname and "entities" in fullname %}
This Solution's Entities
------------------------

.. entity-catalog::

Entity Relationships
~~~~~~~~~~~~~~~~~~~~

.. entity-diagram::

{% elif "use_case" in fullname and "entities" in fullname %}
This Solution's Use Cases
-------------------------

.. usecase-catalog::

{% elif "repository" in fullname and "entities" in fullname %}
This Solution's Repository Protocols
-------------------------------------

.. repository-catalog::

{% elif "service_protocol" in fullname and "entities" in fullname %}
This Solution's Service Protocols
---------------------------------

.. service-protocol-catalog::

{% endif %}
