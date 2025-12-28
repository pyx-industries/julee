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

{% if "persona" in fullname and "entities" in fullname %}
This Solution's Personas
------------------------

.. persona-index::

Persona Overview
~~~~~~~~~~~~~~~~

.. persona-index-diagram::

{% elif "journey" in fullname and "entities" in fullname %}
This Solution's Journeys
------------------------

.. journey-index::

Journey Dependencies
~~~~~~~~~~~~~~~~~~~~

.. journey-dependency-graph::

{% elif "epic" in fullname and "entities" in fullname %}
This Solution's Epics
---------------------

.. epic-index::

{% elif "story" in fullname and "entities" in fullname %}
This Solution's Stories
-----------------------

.. story-index::

{% elif "app" in fullname and "entities" in fullname %}
This Solution's Apps
--------------------

.. app-index::

Apps by Interface
~~~~~~~~~~~~~~~~~

.. app-list-by-interface::

{% elif "accelerator" in fullname and "entities" in fullname %}
This Solution's Accelerators
----------------------------

.. accelerator-index::

Accelerator Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

.. accelerator-dependency-diagram::

{% elif "integration" in fullname and "entities" in fullname %}
This Solution's Integrations
----------------------------

.. integration-index::

{% elif "contrib" in fullname and "entities" in fullname %}
This Solution's Contribs
------------------------

.. contrib-index::

{% endif %}
