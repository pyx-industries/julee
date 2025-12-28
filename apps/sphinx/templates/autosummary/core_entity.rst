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

{% if "bounded_context" in fullname %}
This Solution's Bounded Contexts
--------------------------------

.. bounded-context-list::

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
