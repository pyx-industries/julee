# PlantUML C4 Syntax Reference

This document describes the C4-PlantUML syntax for creating software architecture diagrams. It uses terminology aligned with the [C4 Fundamentals](./c4_fundamentals.md) research report.

---

## 1. Overview

**C4-PlantUML** combines PlantUML's diagram-as-code approach with the C4 model's abstraction hierarchy. It provides macros for each C4 abstraction (Person, Software System, Container, Component) and diagram type.

### Key Benefits

- **Version control friendly:** Diagrams defined in text files
- **Consistent notation:** Standardised macros ensure uniform styling
- **Tooling integration:** Works with PlantUML renderers, IDE plugins, CI/CD pipelines

---

## 2. Including the Library

Each diagram type requires a specific include file:

```plantuml
' System Context diagrams
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

' Container diagrams (includes Context elements)
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

' Component diagrams (includes Container and Context elements)
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

' Dynamic diagrams
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Dynamic.puml

' Deployment diagrams
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Deployment.puml
```

Each include file builds on the previous level, so `C4_Component.puml` includes all macros from Container and Context levels.

---

## 3. Core Abstraction Macros

### 3.1 Person

Represents human users of the software system.

```plantuml
Person(alias, "Label", "Description")
Person_Ext(alias, "Label", "Description")    ' External person
```

**Full signature:**
```plantuml
Person(alias, label, ?descr, ?sprite, ?tags, ?link, ?type)
```

### 3.2 Software System

The highest abstraction level—something that delivers value to users.

```plantuml
System(alias, "Label", "Description")
System_Ext(alias, "Label", "Description")    ' External system

' Specialised variants
SystemDb(alias, "Label", "Description")      ' Database system
SystemQueue(alias, "Label", "Description")   ' Queue/messaging system
SystemDb_Ext(alias, "Label", "Description")
SystemQueue_Ext(alias, "Label", "Description")
```

**Full signature:**
```plantuml
System(alias, label, ?descr, ?sprite, ?tags, ?link, ?type, ?baseShape)
```

### 3.3 Container

Runtime boundary—an application or data store that needs to be running.

```plantuml
Container(alias, "Label", "Technology", "Description")
Container_Ext(alias, "Label", "Technology", "Description")

' Specialised variants
ContainerDb(alias, "Label", "Technology", "Description")     ' Database
ContainerQueue(alias, "Label", "Technology", "Description")  ' Message queue
ContainerDb_Ext(alias, "Label", "Technology", "Description")
ContainerQueue_Ext(alias, "Label", "Technology", "Description")
```

**Full signature:**
```plantuml
Container(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
```

### 3.4 Component

Grouping of related functionality behind a well-defined interface.

```plantuml
Component(alias, "Label", "Technology", "Description")
Component_Ext(alias, "Label", "Technology", "Description")

' Specialised variants
ComponentDb(alias, "Label", "Technology", "Description")
ComponentQueue(alias, "Label", "Technology", "Description")
ComponentDb_Ext(alias, "Label", "Technology", "Description")
ComponentQueue_Ext(alias, "Label", "Technology", "Description")
```

**Full signature:**
```plantuml
Component(alias, label, ?techn, ?descr, ?sprite, ?tags, ?link, ?baseShape)
```

---

## 4. Relationship Macros

Relationships connect elements and describe interactions.

### 4.1 Basic Relationships

```plantuml
Rel(from, to, "Label")
Rel(from, to, "Label", "Technology")
Rel(from, to, "Label", "Technology", "Description")

BiRel(from, to, "Label")    ' Bidirectional relationship
```

**Full signature:**
```plantuml
Rel(from, to, label, ?techn, ?descr, ?sprite, ?tags, ?link)
```

### 4.2 Directional Relationships

Control layout positioning with directional variants:

```plantuml
Rel_U(from, to, "Label")    ' Up
Rel_D(from, to, "Label")    ' Down
Rel_L(from, to, "Label")    ' Left
Rel_R(from, to, "Label")    ' Right

' Bidirectional variants
BiRel_U(from, to, "Label")
BiRel_D(from, to, "Label")
BiRel_L(from, to, "Label")
BiRel_R(from, to, "Label")
```

### 4.3 Relationship Best Practices

- **Include technology:** `Rel(web, api, "Calls", "HTTPS/JSON")`
- **Be specific:** Avoid "Uses"—prefer "Reads from", "Submits to", "Queries"
- **Show direction:** Use directional macros to improve layout

---

## 5. Boundary Macros

Boundaries group related elements within a scope.

### 5.1 Standard Boundaries

```plantuml
' Generic boundary
Boundary(alias, "Label") {
    ' Elements inside
}

' Typed boundaries
Enterprise_Boundary(alias, "Label") {
    ' Organisation scope
}

System_Boundary(alias, "Label") {
    ' Software system scope
}

Container_Boundary(alias, "Label") {
    ' Container scope (for component diagrams)
}
```

**Full signature:**
```plantuml
Boundary(alias, label, ?type, ?tags, ?link, ?descr)
```

### 5.2 Boundary in Sequence Diagrams

For sequence diagrams, boundaries use different syntax:

```plantuml
Boundary(alias, "Label")
' ... elements ...
Boundary_End()
```

---

## 6. Deployment Diagram Elements

For infrastructure and deployment views.

### 6.1 Deployment Nodes

```plantuml
Deployment_Node(alias, "Label", "Type", "Description") {
    ' Nested nodes or containers
}

' Shorthand
Node(alias, "Label", "Type", "Description")

' Directional variants for layout
Node_L(alias, "Label", "Type", "Description")
Node_R(alias, "Label", "Type", "Description")
```

**Full signature:**
```plantuml
Deployment_Node(alias, label, ?type, ?descr, ?sprite, ?tags, ?link)
```

### 6.2 Nested Deployment Structure

Deployment nodes can be nested to represent infrastructure hierarchy:

```plantuml
Deployment_Node(dc, "Data Centre", "Physical") {
    Deployment_Node(server, "Web Server", "Ubuntu 22.04") {
        Deployment_Node(runtime, "Docker", "Container Runtime") {
            Container(api, "API", "Python/FastAPI", "Handles requests")
        }
    }
}
```

---

## 7. Dynamic Diagram Elements

For showing runtime interactions with numbered sequences.

### 7.1 Indexed Relationships

```plantuml
!include C4_Dynamic.puml

' Relationships are automatically numbered
Rel(user, web, "1. Opens browser")
Rel(web, api, "2. Submits request")
Rel(api, db, "3. Queries data")
Rel(api, web, "4. Returns response")
```

### 7.2 Index Control

```plantuml
Index($offset=1)           ' Offset numbering
SetIndex($new_index)       ' Set specific index
LastIndex()                ' Get last index used

' Macros (lowercase)
increment($offset=1)
setIndex($new_index)
```

### 7.3 Dynamic Diagram Example

```plantuml
@startuml
!include C4_Dynamic.puml

ContainerDb(db, "Database", "PostgreSQL")
Container(api, "API", "FastAPI")
Container(web, "Web App", "React")
Person(user, "User")

Rel(user, web, "Opens application")
Rel(web, api, "Submits credentials", "HTTPS")
Rel(api, db, "SELECT * FROM users", "SQL")
Rel(api, web, "Returns JWT token")

SHOW_LEGEND()
@enduml
```

---

## 8. Layout Control

### 8.1 Global Layout

```plantuml
LAYOUT_TOP_DOWN()      ' Default: elements flow top to bottom
LAYOUT_LEFT_RIGHT()    ' Elements flow left to right
LAYOUT_LANDSCAPE()     ' Landscape orientation
```

### 8.2 Element Positioning

Force relative positioning between elements:

```plantuml
Lay_U(from, to)        ' Position 'to' above 'from'
Lay_D(from, to)        ' Position 'to' below 'from'
Lay_L(from, to)        ' Position 'to' left of 'from'
Lay_R(from, to)        ' Position 'to' right of 'from'

Lay_Distance(from, to, ?distance)  ' Control spacing
```

---

## 9. Styling and Customisation

### 9.1 Element Tags

Create custom styles with tags:

```plantuml
' Define tag styles
AddElementTag("critical", $bgColor="red", $fontColor="white", $borderColor="darkred")
AddElementTag("deprecated", $bgColor="grey", $fontColor="white")

' Apply to elements
Container(api, "API", "FastAPI", "Core service", $tags="critical")
Container(legacy, "Legacy", "PHP", "Old system", $tags="deprecated")
```

**Full signature:**
```plantuml
AddElementTag(tagStereo, ?bgColor, ?fontColor, ?borderColor, ?sprite, ?legendText)
```

### 9.2 Relationship Tags

```plantuml
AddRelTag("async", $textColor="blue", $lineColor="blue", $lineStyle="dashed")
AddRelTag("sync", $textColor="black", $lineColor="black")

Rel(a, b, "Publishes event", $tags="async")
Rel(c, d, "Calls directly", $tags="sync")
```

### 9.3 Boundary Tags

```plantuml
AddBoundaryTag("external", $bgColor="lightgrey", $borderColor="grey")

System_Boundary(ext, "External Systems", $tags="external") {
    System_Ext(s1, "Third Party API")
}
```

### 9.4 Update Default Styles

```plantuml
UpdateElementStyle(elementName, ?bgColor, ?fontColor, ?borderColor, ?sprite)
UpdateRelStyle(textColor, lineColor)
UpdateBoundaryStyle(?elementName, ?bgColor, ?fontColor, ?borderColor)
```

---

## 10. Legend and Display Options

### 10.1 Legend

```plantuml
SHOW_LEGEND()                              ' Standard legend
SHOW_LEGEND(?hideStereotype, ?details)     ' With options
LAYOUT_WITH_LEGEND()                       ' Legend integrated in layout
SHOW_FLOATING_LEGEND(?alias, ?hideStereotype, ?details)
```

### 10.2 Display Control

```plantuml
HIDE_STEREOTYPE()          ' Hide stereotype labels
SHOW_PERSON_SPRITE(?sprite)
HIDE_PERSON_SPRITE()
```

---

## 11. Complete Examples

### 11.1 System Context Diagram

```plantuml
@startuml System Context
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title System Context Diagram - Julee Platform

Person(user, "Platform User", "Submits documents for processing")
Person(admin, "Administrator", "Configures processing pipelines")

System(julee, "Julee Platform", "Document processing and assembly system")

System_Ext(temporal, "Temporal", "Workflow orchestration")
System_Ext(anthropic, "Anthropic API", "AI/ML knowledge service")
System_Ext(minio, "MinIO", "Object storage")

Rel(user, julee, "Uploads documents", "HTTPS")
Rel(admin, julee, "Configures pipelines", "HTTPS")
Rel(julee, temporal, "Executes workflows")
Rel(julee, anthropic, "Queries knowledge", "HTTPS")
Rel(julee, minio, "Stores objects", "S3 API")

SHOW_LEGEND()
@enduml
```

### 11.2 Container Diagram

```plantuml
@startuml Container Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title Container Diagram - Julee Platform

Person(user, "User")

System_Boundary(julee, "Julee Platform") {
    Container(api, "API", "FastAPI", "REST endpoints for document management")
    Container(worker, "Worker", "Temporal Worker", "Executes workflow activities")
    ContainerDb(minio, "Object Store", "MinIO", "Document and config storage")
}

System_Ext(temporal, "Temporal Server", "Workflow orchestration")
System_Ext(anthropic, "Anthropic API", "Knowledge service")

Rel(user, api, "Uses", "HTTPS")
Rel(api, temporal, "Starts workflows")
Rel(worker, temporal, "Polls for tasks")
Rel_R(api, minio, "Reads/Writes", "S3 API")
Rel_R(worker, minio, "Reads/Writes", "S3 API")
Rel(worker, anthropic, "Queries", "HTTPS")

SHOW_LEGEND()
@enduml
```

### 11.3 Component Diagram

```plantuml
@startuml Component Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram - API Container

Container_Boundary(api, "API Container") {
    Component(routers, "Routers", "FastAPI", "HTTP endpoint handlers")
    Component(deps, "Dependencies", "Python", "Dependency injection container")
    Component(use_cases, "Use Cases", "Python", "Business logic orchestration")
    Component(repos, "Repositories", "Python", "Data access abstraction")
}

ContainerDb(minio, "MinIO", "S3")
Container(temporal, "Temporal", "Workflow")

Rel(routers, deps, "Injects")
Rel(routers, use_cases, "Invokes")
Rel(use_cases, repos, "Uses")
Rel(repos, minio, "Persists to", "S3 API")
Rel(routers, temporal, "Starts workflows")

SHOW_LEGEND()
@enduml
```

### 11.4 Dynamic Diagram

```plantuml
@startuml Dynamic Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Dynamic.puml

title Document Processing Flow

Person(user, "User")
Container(api, "API", "FastAPI")
Container(worker, "Worker", "Temporal")
ContainerDb(minio, "MinIO", "S3")
System_Ext(anthropic, "Anthropic", "AI")

Rel(user, api, "1. Uploads document", "HTTPS")
Rel(api, minio, "2. Stores document", "S3")
Rel(api, worker, "3. Triggers workflow", "Temporal")
Rel(worker, minio, "4. Retrieves document", "S3")
Rel(worker, anthropic, "5. Extracts content", "HTTPS")
Rel(worker, minio, "6. Saves assembly", "S3")

SHOW_LEGEND()
@enduml
```

### 11.5 Deployment Diagram

```plantuml
@startuml Deployment Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Deployment.puml

title Deployment Diagram - Production

Deployment_Node(cloud, "Cloud Provider", "AWS/GCP") {
    Deployment_Node(k8s, "Kubernetes Cluster", "EKS/GKE") {
        Deployment_Node(api_pod, "API Pod", "Docker") {
            Container(api, "API", "FastAPI")
        }
        Deployment_Node(worker_pod, "Worker Pod", "Docker") {
            Container(worker, "Worker", "Temporal Worker")
        }
    }
    Deployment_Node(temporal_node, "Temporal", "Managed Service") {
        Container(temporal, "Temporal Server", "Go")
    }
    Deployment_Node(storage, "Storage", "Managed") {
        ContainerDb(minio, "MinIO", "S3-compatible")
        ContainerDb(postgres, "PostgreSQL", "Temporal backend")
    }
}

Rel(api, temporal, "Submits workflows")
Rel(worker, temporal, "Polls tasks")
Rel(api, minio, "Stores documents")
Rel(worker, minio, "Reads documents")
Rel(temporal, postgres, "Persists state")

SHOW_LEGEND()
@enduml
```

---

## 12. Diagram Type Summary

| Diagram Type | Include File | Primary Elements | Purpose |
|--------------|--------------|------------------|---------|
| **System Context** | `C4_Context.puml` | Person, System, System_Ext | Show system in relation to users and external systems |
| **Container** | `C4_Container.puml` | + Container, ContainerDb, ContainerQueue | Show major applications and data stores |
| **Component** | `C4_Component.puml` | + Component, ComponentDb, ComponentQueue | Show components within a container |
| **Dynamic** | `C4_Dynamic.puml` | All elements + indexed Rel | Show runtime interactions with sequencing |
| **Deployment** | `C4_Deployment.puml` | Deployment_Node, Node + Containers | Show infrastructure and deployment topology |

---

## 13. Authoritative Sources

### Primary Reference
- **C4-PlantUML GitHub:** https://github.com/plantuml-stdlib/C4-PlantUML
- **C4-PlantUML Documentation Site:** https://plantuml-stdlib.github.io/C4-PlantUML/

### Sample Diagrams
- **Container Example:** https://github.com/plantuml-stdlib/C4-PlantUML/blob/master/samples/
- **Layout Options:** https://github.com/plantuml-stdlib/C4-PlantUML/blob/master/LayoutOptions.md

### Tutorials
- **Hitchhiker's Guide to PlantUML C4:** https://crashedmind.github.io/PlantUMLHitchhikersGuide/C4/C4Stdlib.html
- **Medium Guide:** https://medium.com/@erickzanetti/understanding-the-c4-model-a-practical-guide-with-plantuml-examples-76cfdcbe0e01

### Related Tools
- **PlantUML:** https://plantuml.com/
- **Structurizr (C4 DSL):** https://structurizr.com/

---

*Document created: 2025-12-19*
*Aligned with [C4 Fundamentals](./c4_fundamentals.md) terminology*
