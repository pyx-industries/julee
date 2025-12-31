"""Unsigned credential service - no-op implementation for development.

This service does NOT actually sign credentials. It's for development
and testing when you don't need real cryptographic proofs.

For production, implement CredentialSigningService with actual
cryptographic signing (e.g., Ed25519 Data Integrity proofs).
"""

from datetime import datetime, timezone

from julee.contrib.untp.entities.core import CredentialProof
from julee.contrib.untp.entities.credential import BaseCredential


class UnsignedCredentialService:
    """No-op credential signing service for development.

    Does not actually sign credentials - just returns them unchanged.
    Use this for testing when you don't need real cryptographic proofs.

    For verification, always returns True (credentials are "valid").
    """

    def __init__(
        self, verification_method: str = "https://example.com/keys/dev"
    ) -> None:
        self._verification_method = verification_method

    async def sign(self, credential: BaseCredential) -> BaseCredential:
        """Return the credential unchanged (no actual signing).

        In a real implementation, this would:
        1. Serialize the credential to canonical form
        2. Sign with a private key
        3. Return a new credential with proof attached

        This implementation just returns the credential as-is.
        """
        return credential

    async def verify(self, credential: BaseCredential) -> bool:
        """Always returns True (no actual verification).

        In a real implementation, this would:
        1. Extract the proof
        2. Verify the signature against the credential content
        3. Return True if valid, False if not

        This implementation always returns True.
        """
        return True

    async def get_verification_method(self) -> str:
        """Return the configured verification method URI."""
        return self._verification_method

    async def create_proof(self, credential: BaseCredential) -> CredentialProof:
        """Return a placeholder proof (no actual cryptographic proof).

        This no-op implementation returns a proof with empty values.
        """
        return CredentialProof(
            proof_type="None",
            created=datetime.now(timezone.utc),
            verification_method=self._verification_method,
            proof_purpose="assertionMethod",
            proof_value="",
        )


class MockSignedCredentialService:
    """Mock signing service that adds a fake proof for testing.

    Adds a proof field to credentials to simulate signing, but the
    proof is not cryptographically valid. Useful for testing code
    paths that depend on credentials having a proof.
    """

    def __init__(
        self, verification_method: str = "https://example.com/keys/test"
    ) -> None:
        self._verification_method = verification_method

    async def sign(self, credential: BaseCredential) -> BaseCredential:
        """Add a mock proof to the credential.

        Creates a fake DataIntegrityProof for testing purposes.
        The proof_value is not a real signature.
        """
        mock_proof = CredentialProof(
            proof_type="DataIntegrityProof",
            created=datetime.now(timezone.utc),
            verification_method=self._verification_method,
            proof_purpose="assertionMethod",
            proof_value="mock-signature-for-testing",
        )

        # Create a new credential with the proof
        # Since credentials are frozen, we need to use model_copy
        return credential.model_copy(update={"proof": mock_proof})

    async def verify(self, credential: BaseCredential) -> bool:
        """Check if the credential has our mock proof.

        Returns True if the credential has a proof with our mock signature.
        Returns False if no proof or different proof.
        """
        if credential.proof is None:
            return False
        return credential.proof.proof_value == "mock-signature-for-testing"

    async def get_verification_method(self) -> str:
        """Return the configured verification method URI."""
        return self._verification_method

    async def create_proof(self, credential: BaseCredential) -> CredentialProof:
        """Create a mock proof for testing.

        Returns a fake DataIntegrityProof for testing purposes.
        """
        return CredentialProof(
            proof_type="DataIntegrityProof",
            created=datetime.now(timezone.utc),
            verification_method=self._verification_method,
            proof_purpose="assertionMethod",
            proof_value="mock-signature-for-testing",
        )
