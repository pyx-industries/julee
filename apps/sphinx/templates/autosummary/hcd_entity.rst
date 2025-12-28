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

{% if "story" in fullname %}
This Solution's Stories
-----------------------

.. story-index::

{% elif "persona" in fullname %}
This Solution's Personas
------------------------

.. persona-index::

{% elif "epic" in fullname %}
This Solution's Epics
---------------------

.. epic-index::

{% elif "journey" in fullname %}
This Solution's Journeys
------------------------

.. journey-index::

{% elif "app" in fullname %}
This Solution's Apps
--------------------

.. app-index::

{% elif "accelerator" in fullname %}
This Solution's Accelerators
----------------------------

.. accelerator-index::

{% elif "integration" in fullname %}
This Solution's Integrations
----------------------------

.. integration-index::

{% elif "contrib" in fullname %}
This Solution's Contribs
------------------------

.. contrib-index::

{% endif %}
