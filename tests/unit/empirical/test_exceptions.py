"""Stage 3G: EmpiricalDataError exception tests."""

from __future__ import annotations

import pytest

from backend.domain.exceptions import DomainError, ValidationError
from backend.empirical.exceptions import EmpiricalDataError


class TestEmpiricalDataError:
    def test_is_domain_error(self) -> None:
        err = EmpiricalDataError("test")
        assert isinstance(err, DomainError)

    def test_carries_message(self) -> None:
        err = EmpiricalDataError("lookup failed for id 'X-001'")
        assert "X-001" in str(err)

    def test_is_not_validation_error(self) -> None:
        """EmpiricalDataError is a data-availability failure, not input validation."""
        err = EmpiricalDataError("not found")
        assert not isinstance(err, ValidationError)

    def test_can_be_raised_and_caught_as_domain_error(self) -> None:
        with pytest.raises(DomainError):
            raise EmpiricalDataError("catalog empty")

    def test_can_be_raised_and_caught_as_empirical_error(self) -> None:
        with pytest.raises(EmpiricalDataError):
            raise EmpiricalDataError("no matching record")
