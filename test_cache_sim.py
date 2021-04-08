"""
Unit tests for cache simulation
"""

import pytest
import datetime
from cache_sim import Cache

req1 = {
    'ID' : 1,
    'timestamp': datetime.datetime.now() - datetime.timedelta(minutes = 60),
    'query': "QRY1"
}

req2 = {
    'ID' : 2,
    'timestamp': req1['timestamp'] + datetime.timedelta(minutes = 10),
    'query': "QRY1"
}

req3 = {
    'ID' : 3,
    'timestamp': req1['timestamp'] + datetime.timedelta(minutes = 11),
    'query': "QRY3s"
}

def test_create_valid_cache():
    cache_tmp = Cache(100, 'LRU', 1)
    assert cache_tmp

def test_create_invalid_cache():
    with pytest.raises(AttributeError):
        cache_tmp = Cache(-100, 'LRU', 1)

    with pytest.raises(AttributeError):
        cache_tmp = Cache(100, 'LRU', -1)

    with pytest.raises(AttributeError):
        cache_tmp = Cache(100, 'INVALID', 1)

def test_miss():
    cache = Cache(100, 'LRU', 1)
    cache.run_request(req1)
    assert cache.count_misses == 1, "expected 1 miss"

def test_hit():
    cache = Cache(100, 'LRU', 1000 )
    cache.run_request(req1)
    cache.run_request(req2)
    assert cache.count_misses == 1, "expected 1 miss as the second request should be cached"

def test_ttl_expiration():
    cache = Cache(100, 'LRU', 9)
    cache.run_request(req1)
    cache.run_request(req2)
    assert cache.count_misses == 2, "expected 2 misses"

def test_displacement():
    cache = Cache(2, 'LRU', 100)
    cache.run_request(req1)
    cache.run_request(req2)
    cache.run_request(req3)
    assert len(cache.cache) == 2, "limited catch size"

def test_streaming_request():
    cache = Cache(2, 'LRU', 100)
    cache.run_requests_from_file('./debug.csv', 1)
    assert len(cache.cache) == 1, "reading one request from file"

def test_streaming_requests():
    cache = Cache(4, 'LRU', 100)
    cache.run_requests_from_file('./debug.csv', 4)
    assert len(cache.cache) == 2, "reading 4 requests from file"