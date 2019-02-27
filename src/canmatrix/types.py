# -*- coding: utf-8 -*-
"""Contains user defined types for more readable type hinting."""
import typing

RawValue = typing.Union[int, float]
PhysicalValue = typing.Any  # more than typing.Union[int, decimal.Decimal, float]
OptionalRawValue = typing.Optional[RawValue]
OptionalPhysicalValue = typing.Optional[PhysicalValue]
