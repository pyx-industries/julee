"""EmitCredentialUseCase - sign and store UNTP credentials.

Signs a credential using the CredentialSigningService and stores it
using the CredentialRepository.
"""

from pydantic import BaseModel

from julee.contrib.untp.entities.credential import BaseCredential
from julee.contrib.untp.repositories.credential import CredentialRepository
from julee.contrib.untp.services.signing import CredentialSigningService
from julee.core.decorators import use_case


class EmitCredentialRequest(BaseModel):
    """Request to emit (sign and store) a credential."""

    credential: BaseCredential
    sign: bool = True


class EmitCredentialResponse(BaseModel):
    """Response from emitting a credential."""

    credential: BaseCredential
    signed: bool
    stored: bool
    credential_id: str


@use_case
class EmitCredentialUseCase:
    """Sign and store a UNTP credential.

    Takes a projected credential, optionally signs it, and stores it
    in the credential repository.

    The signing step can be skipped for development/testing by setting
    sign=False in the request.
    """

    def __init__(
        self,
        credential_repo: CredentialRepository,
        signing_service: CredentialSigningService | None = None,
    ) -> None:
        self.credential_repo = credential_repo
        self.signing_service = signing_service

    async def execute(self, request: EmitCredentialRequest) -> EmitCredentialResponse:
        """Sign and store a credential.

        Args:
            request: Contains the credential to emit

        Returns:
            Response with the emitted credential
        """
        credential = request.credential
        signed = False

        # Sign the credential if requested and signing service available
        if request.sign and self.signing_service is not None:
            credential = await self.signing_service.sign(credential)
            signed = True

        # Store the credential
        await self.credential_repo.save(credential)

        return EmitCredentialResponse(
            credential=credential,
            signed=signed,
            stored=True,
            credential_id=credential.id,
        )


class EmitMultipleCredentialsRequest(BaseModel):
    """Request to emit multiple credentials."""

    credentials: list[BaseCredential]
    sign: bool = True


class EmitMultipleCredentialsResponse(BaseModel):
    """Response from emitting multiple credentials."""

    credentials: list[BaseCredential]
    signed_count: int
    stored_count: int
    credential_ids: list[str]


@use_case
class EmitMultipleCredentialsUseCase:
    """Sign and store multiple UNTP credentials.

    Batch operation for emitting multiple credentials from a single
    use case execution (which can produce multiple events).
    """

    def __init__(
        self,
        credential_repo: CredentialRepository,
        signing_service: CredentialSigningService | None = None,
    ) -> None:
        self.credential_repo = credential_repo
        self.signing_service = signing_service

    async def execute(
        self, request: EmitMultipleCredentialsRequest
    ) -> EmitMultipleCredentialsResponse:
        """Sign and store multiple credentials.

        Args:
            request: Contains the credentials to emit

        Returns:
            Response with the emitted credentials
        """
        result_credentials: list[BaseCredential] = []
        signed_count = 0

        for credential in request.credentials:
            if request.sign and self.signing_service is not None:
                credential = await self.signing_service.sign(credential)
                signed_count += 1

            await self.credential_repo.save(credential)
            result_credentials.append(credential)

        return EmitMultipleCredentialsResponse(
            credentials=result_credentials,
            signed_count=signed_count,
            stored_count=len(result_credentials),
            credential_ids=[c.id for c in result_credentials],
        )
