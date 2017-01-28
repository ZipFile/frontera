from __future__ import absolute_import
from frontera.core import OverusedBuffer
from frontera.core.models import Request
from six.moves import range

from tests import mock


call = mock.call
Mock = mock.Mock

r1 = Request('http://www.example.com')
r2 = Request('http://www.example.com/some/')
r3 = Request('htttp://www.example.com/some/page/')
r4 = Request('http://example.com')
r5 = Request('http://example.com/some/page')
r6 = Request('http://example1.com')


class TestOverusedBuffer(object):

    requests = []

    def get_func(self, max_n_requests, **kwargs):
        lst = []
        for _ in range(max_n_requests):
            if self.requests:
                lst.append(self.requests.pop())
        return lst

    def test(self):
        log = Mock()
        log.isEnabledFor.return_value = True

        ob = OverusedBuffer(self.get_func, logger=log)
        self.requests = [r1, r2, r3, r4, r5, r6]

        assert set(ob.get_next_requests(10, overused_keys=['www.example.com', 'example1.com'],
                                        key_type='domain')) == set([r4, r5])
        assert log.debug.mock_calls == [
            call("Overused keys: %s", "['www.example.com', 'example1.com']"),
            call("Pending: %d", 0),
        ]
        log.reset_mock()

        assert ob.get_next_requests(10, overused_keys=['www.example.com'],
                                    key_type='domain') == [r6]
        assert log.debug.mock_calls == [
            call("Overused keys: %s", "['www.example.com']"),
            call("Pending: %d", 4),
        ]
        log.reset_mock()

        assert ob.get_next_requests(10, overused_keys=['www.example.com'],
                                    key_type='domain') == []
        assert log.debug.mock_calls == [
            call("Overused keys: %s", "['www.example.com']"),
            call("Pending: %d", 3),
        ]
        log.reset_mock()

        #the max_next_requests is 3 here to cover the "len(requests) == max_next_requests" case.
        assert set(ob.get_next_requests(3, overused_keys=['example.com'],
                                        key_type='domain')) == set([r1, r2, r3])
        assert log.debug.mock_calls == [
            call("Overused keys: %s", "['example.com']"),
            call("Pending: %d", 3),
        ]
        log.reset_mock()

        assert ob.get_next_requests(10, overused_keys=[], key_type='domain') == []
        assert log.debug.mock_calls == [
            call("Overused keys: %s", "[]"),
            call("Pending: %d", 0),
        ]
