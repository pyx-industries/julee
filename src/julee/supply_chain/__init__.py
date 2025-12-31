"""Supply Chain bounded context.

Models business processes as supply chains with provenance tracking.
Supports UN Transparency Protocol (UNTP) and W3C Verifiable Credentials.

Core concept: An Accelerator is a collection of business processes
(implemented as pipelines) that form a supply chain. The execution
of these processes produces verifiable credentials, enabling
transparent, traceable, and trusted digital products.

Future entities:
- Credential: W3C Verifiable Credential produced by process execution
- ProductPassport: Digital Product Passport with provenance graph
- TrustGraph: Graph of claims about how outcomes were produced
"""
