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

{% if "software_system" in fullname and "entities" in fullname %}
This Solution's Software Systems
--------------------------------

.. software-system-index::

System Landscape
~~~~~~~~~~~~~~~~

.. system-landscape-diagram::

{% elif "container" in fullname and "entities" in fullname %}
This Solution's Containers
--------------------------

.. container-index::

{% elif "component" in fullname and "entities" in fullname %}
This Solution's Components
--------------------------

.. component-index::

{% elif "relationship" in fullname and "entities" in fullname %}
This Solution's Relationships
-----------------------------

.. relationship-index::

{% elif "deployment_node" in fullname and "entities" in fullname %}
This Solution's Deployment Nodes
--------------------------------

.. deployment-node-index::

{% elif "dynamic_step" in fullname and "entities" in fullname %}
This Solution's Dynamic Steps
-----------------------------

Dynamic steps are shown in context of their dynamic diagrams.

{% elif "diagrams" in fullname and "entities" in fullname %}
C4 Diagram Types
----------------

This module defines the diagram domain models used for rendering C4 diagrams.

{% endif %}
