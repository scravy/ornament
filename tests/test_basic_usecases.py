from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime

from apm import *


class BasicUseCases(unittest.TestCase):

    def test_dict(self):
        self.assertTrue(match(
            {"foo": 1, "bar": 2, "baz": 3, "quux": 4},
            {"foo": 1}
        ))
        self.assertFalse(match(
            {"foo": 1, "bar": 2, "baz": 3, "quux": 4},
            Strict({"foo": 1})
        ))
        positive_number = InstanceOf(int) & Check(lambda v: v >= 0)
        self.assertTrue(match(
            {"foo": 1, "bar": 2},
            Strict({"foo": positive_number, "bar": positive_number})
        ))

    def test_tuple(self):
        self.assertTrue(match(
            (1, 2),
            (..., ...)
        ))

    def test_strict(self):
        self.assertTrue(match(1, 1.0))
        self.assertTrue(match(1.0, Strict(1.0)))
        self.assertTrue(match(1, Strict(1)))
        self.assertFalse(match(1, Strict(1.0)))

    def test_truish(self):
        self.assertTrue(match(1, Truish()))
        self.assertTrue(match(2.9, Truish()))
        self.assertFalse(match("", Truish()))

    def test_length(self):
        self.assertTrue(match([], Length(0)))
        self.assertTrue(match(('abc',), Length(1)))
        self.assertTrue(match('abc', Length(3)))
        self.assertTrue(match('abc', Length(at_least=1, at_most=4)))
        self.assertFalse(match('abc', Length(at_least=4, at_most=10)))
        self.assertTrue(match('abcde', Length(at_least=4, at_most=5)))
        self.assertFalse(match('abcdef', Length(at_least=4, at_most=5)))

    def test_contains(self):
        self.assertTrue(match([1, 2, 3], Contains(2) & Contains(3)))
        self.assertTrue(match((1, 2, 3), Contains(2) & Contains(3)))
        self.assertTrue(match({1, 2, 3}, Contains(2) & Contains(3)))
        self.assertTrue(match({1: 'a', 2: 'b', 3: 'c'}, Contains(2) & Contains(3)))
        self.assertTrue(match("quux", Contains('uu')))

    def test_regex(self):
        self.assertTrue(match(
            "Hello, World!",
            Regex("[A-Z][a-z]+, [A-Z][a-z]+!")
        ))
        self.assertFalse(match(
            "Hello, World! How are you today?",
            Regex("[A-Z][a-z]+, [A-Z][a-z]+!")
        ))
        self.assertTrue(match(
            "Hello, World! How are you today?",
            Regex("[A-Z][a-z]+, [A-Z][a-z]+!.*")
        ))

    def test_remaining(self):
        self.assertTrue(match(
            [1, 2, 3, 4],
            [1, 2, 3, Remaining(InstanceOf(int), at_least=1)]))
        self.assertTrue(match(
            [1, 2, 3],
            [1, 2, 3, Remaining(InstanceOf(int))]))
        self.assertTrue(match(
            [1, 2, 3, 4, 5],
            [1, 2, 3, Remaining(InstanceOf(int) & Between(1, 10))]))
        self.assertFalse(match(
            [1, 2, 3, 4, 5],
            [1, 2, 3, Remaining(InstanceOf(int) & Between(1, 3))]))
        self.assertFalse(match(
            [1, 2, 3, 4],
            [1, 2, 3, Remaining(InstanceOf(int), at_least=2)]))

    def test_remaining_with_range(self):
        self.assertTrue(match(
            range(1, 5),
            [1, 2, 3, Remaining(InstanceOf(int), at_least=1)]))
        self.assertTrue(match(
            range(1, 4),
            [1, 2, 3, Remaining(InstanceOf(int))]))
        self.assertTrue(match(
            range(1, 5),
            [1, 2, 3, Remaining(InstanceOf(int) & Between(1, 10))]))
        self.assertFalse(match(
            range(1, 5),
            [1, 2, 3, Remaining(InstanceOf(int) & Between(1, 3))]))
        self.assertFalse(match(
            range(1, 5),
            [1, 2, 3, Remaining(InstanceOf(int), at_least=2)]))

    def test_capture(self):
        self.assertTrue(result := match(
            {
                "This": "Is A Rather Complex Beast",
                "Created-At": "Sun Jan  3 04:08:57 CET 2021",
                "User": {
                    "UserId": 102384,
                    "FirstName": "Jane",
                    "LastName": "Doe",
                }
            },
            {
                "User": Capture({
                    "FirstName": Capture(..., name="first_name"),
                    "LastName": Capture(..., name="last_name"),
                }, name="user")
            }
        ))
        self.assertEqual("Jane", result['first_name'])
        self.assertEqual("Doe", result['last_name'])
        self.assertEqual(102384, result['user']['UserId'])

    def test_remaining_with_capture(self):
        self.assertTrue(result := match(
            [1, 2, 3, 4],
            [1, 2, Capture(Remaining(...), name="tail")]
        ))
        self.assertEqual([3, 4], result['tail'])

    def test_and(self):
        self.assertFalse(match(
            0,
            Between(0, 1) & Between(1, 2)
        ))
        self.assertTrue(match(
            1,
            Between(0, 1) & Between(1, 2)
        ))
        self.assertFalse(match(
            2,
            Between(0, 1) & Between(1, 2)
        ))

    def test_or(self):
        self.assertTrue(match(
            0,
            Between(0, 1) | Between(1, 2)
        ))
        self.assertTrue(match(
            1,
            Between(0, 1) | Between(1, 2)
        ))
        self.assertTrue(match(
            2,
            Between(0, 1) | Between(1, 2)
        ))

    def test_xor(self):
        self.assertTrue(match(
            0,
            Between(0, 1) ^ Between(1, 2)
        ))
        self.assertFalse(match(
            1,
            Between(0, 1) ^ Between(1, 2)
        ))
        self.assertTrue(match(
            2,
            Between(0, 1) ^ Between(1, 2)
        ))

    def test_each(self):
        self.assertTrue(match([1, 2, 3], Each(InstanceOf(int))))
        self.assertFalse(match([1, 2.0, 3], Each(InstanceOf(int))))

    def test_each_item(self):
        pattern = EachItem(Regex("[a-z]+"), InstanceOf(int))
        self.assertTrue(match({"a": 1, "b": 2}, pattern))
        self.assertFalse(match({"_a": 1, "b": 2}, pattern))

    def test_transformed(self):
        self.assertTrue(match("value", Transformed(len, 5)))

    def test_arguments(self):
        # noinspection PyUnusedLocal
        def f(x: int, y: str):
            pass

        # noinspection PyUnusedLocal
        def g(x):
            pass

        # noinspection PyUnusedLocal
        def h(x, y: int, m: str, n: str):
            pass

        self.assertTrue(match(f, Arguments(int, str)))
        self.assertFalse(match(g, Arguments(int)))
        self.assertTrue(match(h, Arguments(None, int, Remaining(str))))

    def test_keyword_arguments(self):
        # noinspection PyUnusedLocal
        def f(x: int, y: bool):
            pass

        self.assertTrue(match(f, Arguments(x=int)))
        self.assertFalse(match(f, Strict(Arguments(x=int))))
        self.assertTrue(match(f, Strict(Arguments(x=int, y=bool))))

    def test_returns(self):
        def f() -> int:
            pass

        self.assertTrue(match(f, Returns(int)))
        self.assertFalse(match(f, Returns(float)))

    def test_at(self):
        record = {
            "foo": {
                "bar": {
                    "quux": {
                        "value": "deeply nested"
                    }
                }
            }
        }

        self.assertTrue(result := match(record, At("foo.bar.quux", {"value": Capture(..., name="value")})))
        self.assertEqual("deeply nested", result['value'])

        self.assertTrue(result := match(record, At(['foo', 'bar', 'quux'], {"value": Capture(..., name="value")})))
        self.assertEqual("deeply nested", result['value'])

        self.assertFalse(match(record, At("foo.bar.quux.baz", InstanceOf(int))))

    def test_string(self):
        path = "https://somehost/foo=1/bar=2/"

        self.assertTrue(result := match(path, String(
            Capture(OneOf("https", "http"), name="protocol"),
            "://",
            Capture(Regex("[a-zA-Z_-]+"), name="host"),
            Regex("/+"),
            "foo=",
            Capture(Regex("[^=/]+"), name="foo"),
            "/",
            "bar=",
            Capture(Regex("[^=/]+"), name="bar"),
            Regex("/*"),
        )))
        self.assertEqual("https", result['protocol'])
        self.assertEqual("somehost", result['host'])
        self.assertEqual("1", result['foo'])
        self.assertEqual("2", result['bar'])

    # noinspection PyUnresolvedReferences
    def test_string_argresult(self):
        path = "https://somehost/foo=1/bar=2/"

        self.assertTrue(result := match(path, String(
            Capture(OneOf("https", "http"), name="protocol"),
            "://",
            Capture(Regex("[a-zA-Z_-]+"), name="host"),
            Regex("/+"),
            "foo=",
            Capture(Regex("[^=/]+"), name="foo"),
            "/",
            "bar=",
            Capture(Regex("[^=/]+"), name="bar"),
            Regex("/*"),
        ), argresult=True))
        self.assertEqual("https", result.protocol)
        self.assertEqual("somehost", result.host)
        self.assertEqual("1", result.foo)
        self.assertEqual("2", result.bar)

    def test_is_type(self):
        self.assertTrue(match(1, IsNumber))
        self.assertTrue(match(1.0, IsNumber))
        self.assertFalse(match(True, IsNumber))

    def test_object(self):
        request = {
            "api_version": "v1",
            "job": {
                "run_at": "2020-08-27 14:09:30",
                "command": "echo 'booya'",
            }
        }

        # noinspection PyUnresolvedReferences
        self.assertTrue(result := match(request, Object(
            api_version="v1",
            job=Object(
                run_at=Transformed(datetime.fromisoformat, 'time' @ _),
            ) & OneOf(
                Object(command='command' @ InstanceOf(str)),
                Object(spawn='container' @ InstanceOf(str)),
            )
        )))
        self.assertFalse('container' in result)
        self.assertEqual(result['time'], datetime(2020, 8, 27, 14, 9, 30))
        self.assertEqual(result['command'], "echo 'booya'")

    def test_transformed_exception(self):
        request = {
            "api_version": "v1",
            "job": {
                "run_at": "junk",
                "command": "echo 'booya'",
            }
        }

        # noinspection PyUnresolvedReferences
        self.assertFalse(match(request, Object(
            job=Object(
                run_at=Transformed(datetime.fromisoformat, 'time' @ _),
            )
        )))

    def test_splat_result(self):
        def f(**kwargs):
            dct = {}
            for k, v in kwargs.items():
                dct[k] = v
            return dct

        self.assertTrue(result := match({'a': 1, 'b': 2, 'c': 3}, Object(a=_ >> 'x', b=_ >> 'y', c=_ >> 'z')))
        r = f(**result)
        self.assertEqual({'x': 1, 'y': 2, 'z': 3}, r)

    def test_maybe(self):
        pattern = Object(a=...) & Maybe(Object(b=_ >> 'capture'))

        self.assertTrue(result := match({'a': 3}, pattern))
        self.assertFalse('capture' in result)
        self.assertTrue(result := match({'a': 3, 'b': 5}, pattern))
        self.assertTrue('capture' in result)
        self.assertEqual(5, result['capture'])

    def test_dataclasses(self):
        @dataclass
        class User:
            first_name: str
            last_name: str

        @dataclass
        class LoggedInUser(User):
            display_name: str

        self.assertTrue(result := match(User("Jane", "Doe"), User("Jane", _ >> 'last_name')))
        self.assertEqual("Doe", result['last_name'])

        self.assertTrue(result := match(LoggedInUser("John", "Doe", "johndoe"), User(_, _ >> 'last_name')))
        self.assertEqual("Doe", result['last_name'])
