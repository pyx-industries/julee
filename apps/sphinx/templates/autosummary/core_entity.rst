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

{% elif "use_case" in fullname and "entities" in fullname %}
This Solution's Use Cases
-------------------------

.. usecase-catalog::

{% elif "repository" in fullname and "entities" in fullname %}
This Solution's Repository Protocols
-------------------------------------

.. repository-catalog::

{% endif %}
