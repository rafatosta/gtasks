"""Google Tasks REST adapter. No GTK or controller dependencies."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

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
                message = "A autorização Google expirou. Reautorize em Contas Online."
            elif error.code == 403:
                message = (
                    "Acesso ao Google Tasks negado. Verifique as permissões da conta "
                    "e se a API Tasks está habilitada."
                )
            elif error.code == 404:
                message = "A lista ou tarefa não existe mais no Google Tasks."
            elif error.code == 429:
                message = "Limite de requisições do Google Tasks atingido. Tente depois."
            else:
                message = f"Erro do Google Tasks (HTTP {error.code})."
            raise GoogleTasksError(message) from None
        except (URLError, TimeoutError, OSError):
            raise GoogleTasksError("Não foi possível conectar ao Google Tasks.") from None
        except (ValueError, UnicodeDecodeError):
            raise GoogleTasksError("Resposta inválida do Google Tasks.") from None

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
        return [
            Task(
                id=item["id"],
                list_id=list_id,
                title=item.get("title") or "",
                completed=item.get("status") == "completed",
            )
            for item in tasks
        ]

    def create_task(self, list_id: str, title: str) -> Task:
        item = self._request(
            "POST", f"/lists/{quote(list_id, safe='')}/tasks", {"title": title}
        )
        return Task(id=item["id"], list_id=list_id, title=item["title"])

    def set_completed(self, list_id: str, task_id: str, completed: bool) -> Task:
        path = (
            f"/lists/{quote(list_id, safe='')}/tasks/"
            f"{quote(task_id, safe='')}"
        )
        payload = {"status": "completed" if completed else "needsAction"}
        item = self._request("PATCH", path, payload)
        return Task(
            id=item["id"],
            list_id=list_id,
            title=item.get("title") or "",
            completed=item.get("status") == "completed",
        )
