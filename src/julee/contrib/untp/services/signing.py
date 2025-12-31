"""CredentialSigningService protocol.

Defines the interface for cryptographically signing UNTP credentials.
"""

from typing import Protocol, runtime_checkable

from julee.contrib.untp.entities.core import CredentialProof
from julee.contrib.untp.entities.credential import BaseCredential


@runtime_checkable
class CredentialSigningService(Protocol):
    """Service protocol for signing UNTP credentials.

    Transforms BaseCredential → BaseCredential with CredentialProof attached.

    Implementations may use various cryptographic methods:
    - Data Integrity proofs (Ed25519, secp256k1)
    - JWT/JWS signatures
    - No-op for development/testing

    The service adds a CredentialProof to the credential, making it a
    Verifiable Credential that can be cryptographically verified.
    """

    async def sign(self, credential: BaseCredential) -> BaseCredential:
        """Sign a credential and return a copy with the proof attached.

        Args:
            credential: The credential to sign (without proof)

        Returns:
            A new credential instance with the proof field populated

        Raises:
            SigningError: If signing fails for any reason
        """
        ...

    async def verify(self, credential: BaseCredential) -> bool:
        """Verify the cryptographic proof on a credential.

        Args:
            credential: The credential to verify (with proof)

        Returns:
            True if the proof is valid, False otherwise

        Raises:
            VerificationError: If verification cannot be performed
        """
        ...

    async def get_verification_method(self) -> str:
        """Get the verification method URI for this service.

        Returns:
            URI of the verification method (public key)
        """
        ...

    async def create_proof(self, credential: BaseCredential) -> CredentialProof:
        """Create a cryptographic proof for a credential.

        Args:
            credential: The credential to create a proof for

        Returns:
            The cryptographic proof (not yet attached to credential)
        """
        ...


class SigningError(Exception):
    """Raised when credential signing fails."""

    pass


class VerificationError(Exception):
    """Raised when credential verification cannot be performed."""

    pass
