UML Ontology and OMG Context
============================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

This document describes the ontological layers of OMG's Unified Modeling
Language (UML) and how they relate to other OMG initiatives. Understanding
this context informs how a UML viewpoint accelerator might be designed
within Julee's projected views architecture.

The Four-Layer Metamodel Architecture
-------------------------------------

OMG uses a four-layer architecture (M0-M3) for modeling standards:

M3: Meta-Object Facility (MOF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The highest ontological layer. MOF is the "meta-metamodel"—the language
used to define metamodels. It is self-describing: MOF defines itself.

**Key Concepts**:

- ``Class`` — defines structure
- ``Association`` — defines relationships
- ``Package`` — grouping mechanism
- ``DataType`` — primitive types

**Role**: MOF provides the foundation for all OMG modeling standards.
UML, BPMN, SysML, and others are all defined in terms of MOF.

M2: Metamodel Layer (UML Specification)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UML specification itself lives at this layer. It defines the vocabulary
and rules for creating UML models.

**Structural Concepts**:

- ``Classifier`` (Class, Interface, DataType, Enumeration)
- ``Feature`` (Property, Operation, Parameter)
- ``Relationship`` (Association, Generalization, Dependency, Realization)

**Behavioral Concepts**:

- ``Activity`` — workflow modeling
- ``StateMachine`` — state-based behavior
- ``Interaction`` — message sequences
- ``UseCase`` — functional requirements

**Packaging Concepts**:

- ``Package`` — namespace and grouping
- ``Component`` — modular unit with interfaces
- ``Node`` — deployment target

M1: User Model Layer
~~~~~~~~~~~~~~~~~~~~

Actual UML diagrams created by practitioners. These are instances of the
UML metamodel.

**Examples**:

- A ``Customer`` class in your domain model
- A ``placeOrder()`` operation
- An association between ``Order`` and ``LineItem``
- A sequence diagram showing checkout flow

M0: Runtime Instance Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~

The actual objects at runtime. Real data flowing through your system.

**Examples**:

- A specific customer "John Smith" (instance of ``Customer``)
- Order #12345 with three line items
- The state of a shopping cart during checkout

Relationship to Other OMG Initiatives
-------------------------------------

MOF-Based Standards
~~~~~~~~~~~~~~~~~~~

All these standards are defined using MOF at M3:

+----------+------------------------------------------+------------------+
| Standard | Purpose                                  | Relation to UML  |
+==========+==========================================+==================+
| **UML**  | General-purpose modeling                 | Core standard    |
+----------+------------------------------------------+------------------+
| **SysML**| Systems engineering                      | UML Profile      |
+----------+------------------------------------------+------------------+
| **BPMN** | Business process modeling                | Separate M2      |
+----------+------------------------------------------+------------------+
| **CWM**  | Data warehousing                         | Separate M2      |
+----------+------------------------------------------+------------------+
| **ODM**  | Ontology definition                      | Separate M2      |
+----------+------------------------------------------+------------------+

UML Profiles
~~~~~~~~~~~~

UML provides a **profile mechanism** for domain-specific extensions without
modifying the core metamodel:

- **Stereotypes**: Extend metaclasses (e.g., ``<<entity>>`` extends Class)
- **Tagged Values**: Add properties to stereotyped elements
- **Constraints**: Restrict how stereotyped elements can be used

**Notable Profiles**:

- **SysML**: Systems engineering (blocks, requirements, parametrics)
- **MARTE**: Real-time and embedded systems
- **SoaML**: Service-oriented architecture
- **UML Testing Profile**: Test specification

XMI and Interchange
~~~~~~~~~~~~~~~~~~~

**XMI (XML Metadata Interchange)** provides serialization:

- Standard format for exchanging models between tools
- Based on MOF structure
- Enables tool interoperability

**OCL (Object Constraint Language)**:

- Formal language for expressing constraints
- Queries over UML models
- Invariants, pre/post conditions

Implications for Julee
----------------------

Why Not Separate MOF and UML Accelerators?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In OMG's world, MOF exists separately because it serves multiple metamodels.
In Julee's context:

1. **UML is sufficient**: We don't need to define arbitrary metamodels
2. **Pragmatic scope**: A curated UML subset covers practical needs
3. **Reduced complexity**: One accelerator instead of two

The UML accelerator effectively *becomes* Julee's M3 by being the language
that can describe other accelerators—including itself.

Collapsing the Layers
~~~~~~~~~~~~~~~~~~~~~

For Julee's purposes, we collapse M3/M2 into a single UML viewpoint::

    OMG World                    Julee World
    ─────────────────────────    ─────────────────────────
    M3: MOF                  ──▶ julee.code (doctrine)
    M2: UML Metamodel        ──▶ julee.uml (viewpoint)
    M1: User Models          ──▶ Projected UML views
    M0: Runtime              ──▶ Running Julee solutions

The ``julee.code`` accelerator provides the foundational concepts (what is
a class, what is a module) that ``julee.uml`` projects into UML notation.

Practical UML Subset
~~~~~~~~~~~~~~~~~~~~

Full UML is large (700+ pages specification). A pragmatic subset for Julee:

**Structural Diagrams**:

- Class Diagram (entities, relationships)
- Component Diagram (bounded contexts, dependencies)
- Package Diagram (module organization)

**Behavioral Diagrams**:

- Use Case Diagram (actors, use cases)
- Sequence Diagram (interactions)
- Activity Diagram (workflows)
- State Machine Diagram (entity states)

**Excluded** (for now):

- Object Diagram (M0 snapshots—less useful for documentation)
- Composite Structure (internal class structure)
- Timing Diagram (real-time constraints)
- Interaction Overview (activity + sequence hybrid)

UML as a Viewpoint Accelerator
------------------------------

Projection Rules
~~~~~~~~~~~~~~~~

The UML viewpoint would define projections from ``julee.code`` concepts::

    julee.code Concept     →    UML Concept
    ───────────────────────────────────────
    BoundedContext         →    Package
    Entity                 →    Class (<<entity>>)
    ValueObject            →    Class (<<valueObject>>)
    Aggregate              →    Class (<<aggregate>>)
    UseCase                →    UseCase
    RepositoryProtocol     →    Interface (<<repository>>)
    ServiceProtocol        →    Interface (<<service>>)
    Property               →    Property
    Method                 →    Operation
    Association            →    Association
    Inheritance            →    Generalization

Serialization
~~~~~~~~~~~~~

UML views could be serialized to multiple formats:

- **PlantUML**: Text-based, version-control friendly
- **Mermaid**: Web-native, simpler syntax
- **XMI**: Standard interchange format
- **SVG**: Direct rendering

The viewpoint defines the *model*; serializers render it to specific formats.

Reflexive Description
~~~~~~~~~~~~~~~~~~~~~

With this architecture:

- ``julee.code`` can be viewed as UML class diagrams
- ``julee.hcd`` can be viewed as UML use case diagrams
- ``julee.c4`` can be viewed as UML component diagrams
- ``julee.uml`` can describe itself in UML

The framework becomes self-documenting through multiple lenses.
