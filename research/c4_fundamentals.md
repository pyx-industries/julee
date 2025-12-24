# C4 Model Fundamentals

This document describes the ontology and key concepts of the C4 model for visualising software architecture.

---

## 1. Overview

The **C4 model** is a lightweight, developer-friendly approach to software architecture diagramming. Created by Simon Brown between 2006 and 2011, it builds on concepts from UML and Philippe Kruchten's 4+1 architectural view model while prioritising simplicity and clarity.

The model addresses a fundamental problem: software teams often produce "a confused mess of boxes and lines" with inconsistent notation, unclear naming, and mixed abstraction levels. C4 restores structured visual communication without unnecessary complexity.

### The Map Analogy

C4 uses an intuitive metaphor: create **maps of your code** at various levels of detail, similar to how Google Maps allows zooming in and out. Each level reveals appropriate detail for different audiences—from executives needing business context to developers diving into component details.

---

## 2. Core Abstractions (Ontology)

The C4 model defines a hierarchy of four abstractions that reflect how architects and developers think about software:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Software System                          │
│  "Delivers value to users, whether human or not"                │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                      Container                          │   │
│   │  "Application or data store; runtime boundary"          │   │
│   │                                                         │   │
│   │   ┌─────────────────────────────────────────────────┐   │   │
│   │   │                   Component                     │   │   │
│   │   │  "Grouping of related functionality behind      │   │   │
│   │   │   a well-defined interface"                     │   │   │
│   │   │                                                 │   │   │
│   │   │   ┌─────────────────────────────────────────┐   │   │   │
│   │   │   │                 Code                    │   │   │   │
│   │   │   │  "Classes, interfaces, functions, etc"  │   │   │   │
│   │   │   └─────────────────────────────────────────┘   │   │   │
│   │   └─────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│     Person      │
│  "Human user"   │
└─────────────────┘
```

### 2.1 Person

A **Person** represents a human user of the software system—actors, roles, personas, or named individuals.

### 2.2 Software System

A **Software System** is the highest level of abstraction. It describes something that delivers value to its users, whether human or not.

**Key characteristics:**
- Typically owned and maintained by a single development team
- Codebase often resides in one repository
- Elements within frequently deploy simultaneously
- The team boundary often aligns with the system boundary

**Not a software system:** Product domains, bounded contexts, business capabilities, feature teams, tribes, or squads.

### 2.3 Container

A **Container** is an application or data store—a runtime boundary around code being executed or data being stored. This has nothing to do with Docker; the term predates containerisation technology.

**Definition:** "Something that needs to be running in order for the overall software system to work."

**Examples:**
- **Applications:** Web applications (server-side or client-side), desktop apps, mobile apps, console applications, serverless functions
- **Data storage:** Databases (MySQL, MongoDB, Oracle), blob stores (Amazon S3), file systems, CDNs
- **Scripts:** Shell scripts and standalone executables

**Key characteristics:**
- Containers are runtime constructs, not code organisation artifacts
- JARs, DLLs, and assemblies are *not* containers—they organise code *within* containers
- A container's logical boundary differs from its physical deployment
- External services (S3, RDS) should be treated as containers when you maintain ownership

### 2.4 Component

A **Component** is a grouping of related functionality encapsulated behind a well-defined interface.

**Key characteristics:**
- Components are *not* separately deployable—all components within a container execute in the same process space
- Exists one level above code, allowing reasoning about functionality without showing individual classes
- Implementation varies by paradigm:
  - Object-oriented: collections of classes and interfaces
  - Procedural: files organised in directories
  - Functional: modules grouping related functions and types

### 2.5 Code

The **Code** level represents individual classes, interfaces, objects, functions, and other implementation details. At this level, UML class diagrams are typically used.

**Note:** This level is optional and rarely recommended for most teams.

---

## 3. Relationships

Relationships connect elements and represent interactions:

- **Direction:** Lines represent unidirectional relationships
- **Labels:** Should match relationship direction and describe intent (dependency or data flow)
- **Technology:** Relationships between containers should have technology/protocol explicitly labelled
- **Clarity:** Avoid vague labels like "Uses"—be specific about what the relationship means

---

## 4. Diagram Types

### 4.1 Core Diagrams (Static Structure)

The four core diagrams correspond to the four abstraction levels:

| Level | Diagram | Purpose |
|-------|---------|---------|
| 1 | **System Context** | Shows software system in relation to users and external systems |
| 2 | **Container** | Illustrates major containers and their interactions within a system |
| 3 | **Component** | Details components within a container and their relationships |
| 4 | **Code** | Lowest-level code structure (optional, rarely used) |

**Guidance:** "You don't need to use all 4 levels of diagram; only those that add value." Most teams find System Context and Container diagrams sufficient.

### 4.2 Supplementary Diagrams

Three additional diagram types provide alternative perspectives:

#### System Landscape Diagram
A map of software systems within an enterprise or organisation scope. Essentially "a system context diagram without a specific focus on a particular software system." Valuable for understanding how multiple systems interconnect.

#### Dynamic Diagram
Illustrates "how elements in the static model collaborate at runtime to implement a user story, use case, feature, etc." Based on UML communication diagrams with numbered interactions indicating ordering.

**Guidance:** Use sparingly—specifically for "interesting/recurring patterns or features that require a complicated set of interactions."

#### Deployment Diagram
Shows "how instances of software systems and/or containers are deployed on to infrastructure within a given deployment environment" (production, staging, development).

**Key elements:**
- **Deployment nodes:** Where software runs—physical servers, VMs, Docker containers, execution environments
- **Infrastructure nodes:** DNS, load balancers, firewalls
- Nodes can be nested hierarchically

---

## 5. Notation Guidelines

The C4 model is **notation-independent** and **tooling-independent**. However:

### 5.1 Required Elements

Every element should include:
- **Name:** Clear, unambiguous identifier
- **Type:** Explicitly specified (Person, Software System, Container, Component)
- **Technology:** For containers and components
- **Description:** Brief text showing key responsibilities

### 5.2 Diagram Requirements

- **Title:** Descriptive, indicating type and scope
- **Key/Legend:** Explaining shapes, colours, line types, arrows
- Acronyms must be explained

### 5.3 Colour and Style

- Any colour scheme is permitted (blue and grey are conventional)
- Maintain consistency within and across diagrams
- Ensure accessibility for colourblind viewers and black/white printing
- Use text over colours to convey meaning

### 5.4 Alternative Notations

Diagrams can use UML, ArchiMate, or interactive visualisations while maintaining C4 abstraction levels.

---

## 6. Key Design Principles

### 6.1 Abstraction-First

The model uses "a common set of abstractions" that mirror how developers think about software. This makes diagrams intuitive for technical audiences.

### 6.2 Hierarchical Zoom

Diagrams are organised hierarchically, enabling "zoom in and zoom out" navigation from high-level context to detailed implementation. Different stakeholders view different levels.

### 6.3 Multiple Targeted Views

C4 "fundamentally rejects the idea of a single overwhelming architectural diagram with everything." Each view is crafted for a specific audience.

### 6.4 Self-Describing Diagrams

Including names, types, technologies, and descriptions on elements "removes much of ambiguity typically seen on software architecture diagrams." Diagrams should be comprehensible with minimal narrative explanation.

---

## 7. How Key Ideas Hang Together

The C4 model forms a coherent system through several interlocking concepts:

```
                    ZOOM LEVELS
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
 Context            Container            Component
 (Who uses it?)     (What runs?)         (How organised?)
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
                    ABSTRACTIONS
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
  Person         Software System         Container
    │                    │                    │
    └──── uses ──────────┘                    │
                         │                    │
                    contains ─────────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
              Component    Component
                    │         │
              contains    contains
                    │         │
                    ▼         ▼
                  Code      Code
```

### The Coherence Model

1. **Abstractions define vocabulary:** Person, Software System, Container, Component, Code provide a shared language for describing architecture.

2. **Containment defines structure:** Each abstraction contains the next level down, creating a clear decomposition hierarchy.

3. **Diagrams define views:** Each diagram type corresponds to an abstraction level, providing the right detail for the right audience.

4. **Relationships define behaviour:** Arrows with descriptions and technology labels show how elements interact.

5. **Supplementary diagrams add perspectives:** Landscape (scope), Dynamic (runtime), and Deployment (infrastructure) views complement the static structure.

### Practical Application

- Start with **System Context** to establish boundaries and external dependencies
- Zoom to **Container** to show internal architecture (where most teams stop)
- Zoom to **Component** only for complex containers requiring detailed design discussion
- Use **Dynamic** diagrams to explain complex runtime scenarios
- Use **Deployment** diagrams for infrastructure and operations discussions

---

## 8. Authoritative Sources

### Primary Sources

- **Official C4 Model Website:** https://c4model.com/
  - Maintained by Simon Brown under Creative Commons license
  - Definitive reference for abstractions, diagrams, and notation

- **Simon Brown's Personal Site:** https://simonbrown.je
  - Author background, workshops, and related resources

### Books

- **"The C4 Model for Visualising Software Architecture"** by Simon Brown
  - Available at: https://leanpub.com/visualising-software-architecture
  - Comprehensive guide with examples

- **O'Reilly "The C4 Model"**
  - https://www.oreilly.com/library/view/the-c4-model/9798341660113/

### Reference Articles

- **InfoQ Article:** https://www.infoq.com/articles/C4-architecture-model/
- **Wikipedia:** https://en.wikipedia.org/wiki/C4_model
- **Baeldung Tutorial:** https://www.baeldung.com/cs/c4-model-abstraction-levels

### Tooling

- **Structurizr:** https://structurizr.com/
  - Simon Brown's tooling for C4 model diagrams
  - DSL for defining architecture as code

- **C4-PlantUML:** https://github.com/plantuml-stdlib/C4-PlantUML
  - PlantUML extension for C4 diagrams

- **IcePanel:** https://icepanel.io/
  - Interactive C4 modelling tool

### Specific Documentation Pages

- Abstractions: https://c4model.com/abstractions
- Software System: https://c4model.com/abstractions/software-system
- Container: https://c4model.com/abstractions/container
- Component: https://c4model.com/abstractions/component
- Diagrams: https://c4model.com/diagrams
- Notation: https://c4model.com/diagrams/notation
- System Landscape: https://c4model.com/diagrams/system-landscape
- Dynamic: https://c4model.com/diagrams/dynamic
- Deployment: https://c4model.com/diagrams/deployment

---

## 9. Historical Context

The C4 model emerged from Simon Brown's work between 2006 and 2011, responding to a gap in the industry:

> "Following the publication of the Manifesto for Agile Software Development in 2001, teams have abandoned UML, discarded the concept of modelling, and instead place a heavy reliance on conversations centered around incoherent whiteboard diagrams or shallow 'Marketecture' diagrams created with Visio."

The model draws inspiration from:
- **UML (Unified Modelling Language):** Rigorous notation, but often too complex
- **4+1 Architectural View Model (Philippe Kruchten):** Multiple views for different stakeholders
- **Ivar Jacobson's work:** Use case diagrams and actor concepts

C4 aimed to be a "lightweight approach to more traditional heavyweight approaches" while retaining their rigour. The official website launch under Creative Commons and a 2018 article popularised the technique.

---

*Document created: 2025-12-19*
*Based on official C4 model documentation and authoritative sources*
