"""Google Tasks REST adapter. No GTK or controller dependencies."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from gtasks.i18n import _
from gtasks.models.google_account import GoogleAccount
from gtasks.models.task import Task
from gtasks.models.task_list import TaskList
from gtasks.repositories.base import TaskRepository


class GoogleTasksError(RuntimeError):
    pass


class GoogleTasksRepository(TaskRepository):
    API = "https://tasks.googleapis.com/tasks/v1"

    def __init__(self, account: GoogleAccount, auth) -> None:
        self._account = account
        self._auth = auth

    def _request(self, method: str, path: str, payload=None, params=None) -> dict:
        url = self.API + path
        if params:
            url += "?" + urlencode(params)

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._auth.get_access_token(self._account)}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=25) as response:
                content = response.read()
                return json.loads(content) if content else {}
        except HTTPError as error:
            if error.code == 401:
                message = _("Google authorization has expired. Authorize the account again in Online Accounts.")
            elif error.code == 403:
                message = (
                    _("Google Tasks access was denied. Check the account permissions and whether the Tasks API is enabled.")
                )
            elif error.code == 404:
                message = _("The list or task no longer exists in Google Tasks.")
            elif error.code == 429:
                message = _("The Google Tasks request limit has been reached. Try again later.")
            else:
                message = _("Google Tasks error (HTTP {code}).").format(code=error.code)
            raise GoogleTasksError(message) from None
        except (URLError, TimeoutError, OSError):
            raise GoogleTasksError(_("Could not connect to Google Tasks.")) from None
        except (ValueError, UnicodeDecodeError):
            raise GoogleTasksError(_("Invalid response from Google Tasks.")) from None

    def _all_items(self, path: str, params=None) -> list[dict]:
        items = []
        token = None
        while True:
            query = dict(params or {})
            if token:
                query["pageToken"] = token
            data = self._request("GET", path, params=query)
            items.extend(data.get("items", []))
            token = data.get("nextPageToken")
            if not token:
                return items

    def list_lists(self) -> list[TaskList]:
        results = self._all_items("/users/@me/lists", {"maxResults": 100})
        return [
            TaskList(id=item["id"], name=item["title"], source=self._account.source)
            for item in results
        ]

    def create_list(self, name: str) -> TaskList:
        item = self._request("POST", "/users/@me/lists", {"title": name})
        return TaskList(id=item["id"], name=item["title"], source=self._account.source)

    def rename_list(self, list_id: str, name: str) -> TaskList:
        item = self._request(
            "PATCH", f"/users/@me/lists/{quote(list_id, safe='')}", {"title": name}
        )
        return TaskList(id=item["id"], name=item["title"], source=self._account.source)

    def delete_list(self, list_id: str) -> None:
        self._request("DELETE", f"/users/@me/lists/{quote(list_id, safe='')}")

    def list_tasks(self, list_id: str) -> list[Task]:
        tasks = self._all_items(
            f"/lists/{quote(list_id, safe='')}/tasks",
            {
                "maxResults": 100,
                "showCompleted": "true",
                "showHidden": "true",
                "showDeleted": "false",
            },
        )
        return [self._task(item, list_id) for item in tasks]

    @staticmethod
    def _task(item: dict, list_id: str) -> Task:
        return Task(
            id=item["id"], list_id=list_id, title=item.get("title") or "",
            completed=item.get("status") == "completed", notes=item.get("notes") or "",
            due=item["due"][:10] if item.get("due") else None,
            parent=item.get("parent"), assigned=bool(item.get("assignmentInfo")),
        )

    def create_task(self, list_id: str, title: str) -> Task:
        item = self._request(
            "POST", f"/lists/{quote(list_id, safe='')}/tasks", {"title": title}
        )
        return self._task(item, list_id)

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task:
        path = (
            f"/lists/{quote(list_id, safe='')}/tasks/"
            f"{quote(task_id, safe='')}"
        )
        payload = {"status": "completed" if completed else "needsAction"}
        item = self._request("PATCH", path, payload)
        return self._task(item, list_id)

    def update_task(self, list_id: str, task_id: str, title: str,
                    notes: str | None, due: str | None) -> Task:
        payload = {"title": title, "due": due + "T00:00:00.000Z" if due else None}
        if notes is not None:
            payload["notes"] = notes
        item = self._request(
            "PATCH", f"/lists/{quote(list_id, safe='')}/tasks/{quote(task_id, safe='')}", payload,
        )
        return self._task(item, list_id)

    def delete_task(self, list_id: str, task_id: str) -> None:
        self._request("DELETE", f"/lists/{quote(list_id, safe='')}/tasks/{quote(task_id, safe='')}")

    def create_subtask(self, list_id: str, parent: str, title: str) -> Task:
        item = self._request("POST", f"/lists/{quote(list_id, safe='')}/tasks",
                             {"title": title}, params={"parent": parent})
        return self._task(item, list_id)

    def move_task(self, list_id: str, task_id: str, destination: str) -> Task:
        item = self._request(
            "POST", f"/lists/{quote(list_id, safe='')}/tasks/{quote(task_id, safe='')}/move",
            params={"destinationTasklist": destination},
        )
        return self._task(item, destination)
