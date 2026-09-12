from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.apps.masters.dto.master import SetPasserellesDTO
from src.apps.masters.exceptions.master_exceptions import InvalidPasserelleTarget
from src.apps.masters.services.master_service import MasterService


def test_set_passerelles_rejects_self_reference():
    """Un master ne peut pas déclarer une passerelle depuis lui-même."""
    master = SimpleNamespace(pubkey="mst_x")
    with pytest.raises(InvalidPasserelleTarget):
        MasterService.set_passerelles(master, SetPasserellesDTO(from_master_pubkeys=["mst_x"]))


@patch("src.apps.masters.services.master_service.Master")
def test_set_passerelles_links_valid_origin_masters(mock_master_cls):
    master = SimpleNamespace(pubkey="mst_y", passerelles_depuis=MagicMock())
    origin = SimpleNamespace(pubkey="mst_x")
    mock_master_cls.objects.filter.return_value.count.return_value = 1
    mock_master_cls.objects.filter.return_value = MagicMock(count=lambda: 1, __iter__=lambda s: iter([origin]))

    MasterService.set_passerelles(master, SetPasserellesDTO(from_master_pubkeys=["mst_x"]))

    master.passerelles_depuis.set.assert_called_once()
