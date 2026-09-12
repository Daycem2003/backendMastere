import uuid

from django.db import IntegrityError, transaction

from src.apps.candidate_profile.models import CandidateProfile
from src.apps.users.dto.user import CreateUserIdentityDTO
from src.apps.users.exceptions.user_exceptions import UserAlreadyExists
from src.apps.users.models import User
from src.shared.exceptions.auth_exceptions import EmailAlreadyExistsException, InactiveUserException, InvalidCredentialsException, UserNotFoundException

from .password_service import PasswordService

# Rôle attribué à tout compte créé via l'inscription publique. Le seul
# endroit du code qui écrit une relation utilisateur → rôle reste
# `authorization` (via `RoleAssignmentService`, appelé par
# `UserProvisioningService` ci-dessous) — `authentication` ne fait que
# choisir *quel* rôle demander, jamais assigner le rôle lui-même.
DEFAULT_REGISTRATION_ROLE_CODE = "CANDIDATE"


class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def register(payload):
        from src.apps.users.services.user_provisioning_service import (
            UserProvisioningService,
        )

        try:
            user = UserProvisioningService.create_user_with_role(
                identity_dto=CreateUserIdentityDTO(
                    email=payload.email,
                    password_hash=PasswordService.hash_password(payload.password),
                ),
                role_code=DEFAULT_REGISTRATION_ROLE_CODE,
                assigned_by=None,
            )
            CandidateProfile.objects.create(
                pubkey=f"cand_{uuid.uuid4().hex[:20]}", user=user, nom=payload.nom,
                prenom=payload.prenom, cin=payload.cin, email=payload.email,
                telephone=payload.telephone, ville=payload.ville,
                annee_naissance=payload.annee_naissance,
            )
        except (UserAlreadyExists, IntegrityError) as error:
            raise EmailAlreadyExistsException() from error
        return user

    @staticmethod
    def login(payload):
        user = User.objects.filter(email=payload.email).first()
        if not user or not PasswordService.verify_password(payload.password, user.password):
            raise InvalidCredentialsException()
        if not user.is_active:
            raise InactiveUserException()
        return user

    @staticmethod
    def initiate_id_number_login(payload) -> None:
        if not CandidateProfile.objects.filter(cin=payload.cin, telephone=payload.telephone).exists():
            raise UserNotFoundException()

    @staticmethod
    def initiate_phone_login(payload) -> None:
        if not CandidateProfile.objects.filter(telephone=payload.telephone).exists():
            raise UserNotFoundException()

    @staticmethod
    def complete_otp_login(telephone: str):
        profile = CandidateProfile.objects.select_related("user").filter(telephone=telephone).first()
        if not profile:
            raise UserNotFoundException()
        if not profile.user.is_active:
            raise InactiveUserException()
        return profile.user

    @staticmethod
    def update_profile(user_pubkey: str, payload) -> None:
        update_data = payload.model_dump(exclude_none=True)
        if not update_data:
            return
        user = User.objects.filter(pubkey=user_pubkey).first()
        if not user:
            raise UserNotFoundException()
        renamed = {"annee_naissance": "annee_naissance", **update_data}
        CandidateProfile.objects.filter(user=user).update(**renamed)
