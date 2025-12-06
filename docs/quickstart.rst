Quick Start
===========

This guide will get you up and running with Julee in minutes.

Starting the System
-------------------

Using Docker Compose (recommended)::

    docker-compose --profile julee up -d

The system includes pre-loaded demo data for immediate exploration.

Using the Demo
--------------

1. **Navigate to the UI**

   Open http://localhost:3000 in your browser.

2. **View Knowledge Services**

   Navigate to the Knowledge Services section to see configured AI services.

3. **Explore Assembly Specifications**

   Go to Specifications to view the pre-configured meeting minutes specification.

4. **Run an Assembly**

   a. Click on the Meeting Minutes specification
   b. Click "Run Assembly"
   c. Select a document from the dropdown
   d. Click "Start Assembly"
   e. Monitor progress in the Temporal UI

5. **View Results**

   Use the API to retrieve the assembled document::

       curl -X GET "http://localhost:8000/documents/<document-id>/content"

Basic Workflow
--------------

Configure Knowledge Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a knowledge service configuration::

    curl -X POST "http://localhost:8000/knowledge_service_configs" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "my-service",
        "service_type": "anthropic",
        "config": {
          "model": "claude-3-5-sonnet-20241022",
          "max_tokens": 4096
        }
      }'

Create Assembly Specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define what data to extract and how to assemble it::

    curl -X POST "http://localhost:8000/assembly_specifications" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "my-spec",
        "description": "Extract structured data",
        "json_schema": {...},
        "queries": [...]
      }'

Upload Document
~~~~~~~~~~~~~~~

Upload a document to process::

    curl -X POST "http://localhost:8000/documents" \\
      -F "file=@document.txt" \\
      -F "name=my-document"

Execute Workflow
~~~~~~~~~~~~~~~~

Trigger the extraction and assembly workflow::

    curl -X POST "http://localhost:8000/workflows/extract-assemble" \\
      -H "Content-Type: application/json" \\
      -d '{
        "document_id": "<document-id>",
        "specification_id": "<spec-id>"
      }'

Next Steps
----------

- Learn about :doc:`architecture/framework`
- Understand :doc:`architecture/deployment`
- Explore the :doc:`autoapi/index`
- Read about :doc:`architecture/workflows`
