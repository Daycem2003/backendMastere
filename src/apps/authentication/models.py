"""Compatibility exports for authentication's domain models."""

from src.apps.candidate_profile.models import CandidateProfile, CandidateStatus
from src.apps.users.models import User, UserRole

UserModel = User
CandidateProfileModel = CandidateProfile
UserRoleEnum = UserRole
CandidateStatusEnum = CandidateStatus

__all__ = ["UserModel", "CandidateProfileModel", "UserRoleEnum", "CandidateStatusEnum"]
