import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from gtasks.models.google_account import GoogleAccount
from gtasks.repositories.google import GoogleTasksRepository


class FakeAuth:
    def get_access_token(self, _account):
        return "test-token"


class FakeResponse:
    def __init__(self, data):
        self._data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self._data


class GoogleRepositoryTest(unittest.TestCase):
    def setUp(self):
        account = GoogleAccount("account-1", "example@test.invalid", "/account/path")
        self.repository = GoogleTasksRepository(account, FakeAuth())

    def test_lists_paginate_and_keep_account_origin(self):
        def fake_open(request, timeout):
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            page = parse_qs(urlsplit(request.full_url).query).get("pageToken")
            if page:
                return FakeResponse({"items": [{"id": "b", "title": "Two"}]})
            return FakeResponse({
                "items": [{"id": "a", "title": "One"}],
                "nextPageToken": "next",
            })

        with patch("gtasks.repositories.google.urlopen", side_effect=fake_open):
            lists = self.repository.list_lists()
        self.assertEqual([item.name for item in lists], ["One", "Two"])
        self.assertEqual([item.source for item in lists], ["google:account-1"] * 2)

    def test_completed_tasks_are_requested_and_parsed(self):
        def fake_open(request, timeout):
            params = parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(params["showCompleted"], ["true"])
            self.assertEqual(params["showHidden"], ["true"])
            return FakeResponse({"items": [
                {"id": "t1", "title": "Finished", "status": "completed"}
            ]})

        with patch("gtasks.repositories.google.urlopen", side_effect=fake_open):
            tasks = self.repository.list_tasks("list-one")
        self.assertTrue(tasks[0].completed)

    def test_creating_task_sends_post(self):
        def fake_open(request, timeout):
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(json.loads(request.data)["title"], "Write tests")
            return FakeResponse({"id": "t1", "title": "Write tests"})

        with patch("gtasks.repositories.google.urlopen", side_effect=fake_open):
            task = self.repository.create_task("list-one", "Write tests")
        self.assertEqual(task.list_id, "list-one")


if __name__ == "__main__":
    unittest.main()
