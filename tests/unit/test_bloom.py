"""
Contains tests for the main bloom filter class.
"""

import pytest
from pyblooming.bloom import BloomFilter

class TestBloomFilter(object):

    def test_required_bits(self):
        """
        Tests that the number of required bits that the bloom filter
        says it needs is correct given some known-sane values.
        """
        pass

    def test_k_less_than_one(self):
        """
        Tests that a bloom filter with a ``k`` less than one will
        cause a problem.
        """
        with pytest.raises(ValueError):
            BloomFilter(k=0)
