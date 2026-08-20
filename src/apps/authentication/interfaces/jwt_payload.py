from typing import Literal, TypedDict


class JwtPayload(TypedDict):
    """
    Forme exacte du contenu encodé dans un JWT émis par ce module.
    `sub` correspond toujours au `pubkey` du User (jamais son id interne).
    """

    sub: str
    role: str
    type: Literal["access", "refresh"]
    exp: int
