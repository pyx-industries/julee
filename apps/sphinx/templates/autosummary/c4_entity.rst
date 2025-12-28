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

{% if "software_system" in fullname %}
This Solution's Software Systems
--------------------------------

.. software-system-index::

{% elif "container" in fullname and "entities" in fullname %}
This Solution's Containers
--------------------------

.. container-index::

{% elif "component" in fullname and "entities" in fullname %}
This Solution's Components
--------------------------

.. component-index::

{% elif "relationship" in fullname %}
This Solution's Relationships
-----------------------------

.. relationship-index::

{% elif "deployment_node" in fullname %}
This Solution's Deployment Nodes
--------------------------------

.. deployment-node-index::

{% endif %}
