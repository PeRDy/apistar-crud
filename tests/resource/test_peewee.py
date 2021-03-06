import typing

import peewee
import pytest
from apistar import App, ASyncApp, Include, TestClient, http, types, validators
from apistar_pagination import PageNumberResponse
from apistar_peewee_orm import PeeweeDatabaseComponent, PeeweeTransactionHook

from apistar_crud.resource.peewee import Resource

database_component = PeeweeDatabaseComponent(url="sqlite+pool://")


class PuppyModel(peewee.Model):
    id = peewee.IntegerField(primary_key=True)
    name = peewee.CharField()

    class Meta:
        database = database_component.database


class PuppyInputType(types.Type):
    id = validators.Integer(allow_null=True, default=None)
    name = validators.String(allow_null=True)


class PuppyOutputType(types.Type):
    id = validators.Integer()
    name = validators.String()


class PuppyResource(metaclass=Resource):
    name = "puppy"
    verbose_name = "Puppy"

    model = PuppyModel
    input_type = PuppyInputType
    output_type = PuppyOutputType
    methods = ("create", "retrieve", "update", "delete", "list", "drop")

    @classmethod
    def list(
        cls, page: http.QueryParam, page_size: http.QueryParam, name: http.QueryParam
    ) -> typing.List[PuppyOutputType]:
        return PageNumberResponse(page=page, page_size=page_size, content=cls._filter(name=name))


routes = [Include("/puppy", "puppy", PuppyResource.routes)]

components = [database_component]
event_hooks = [PeeweeTransactionHook()]

app = App(routes=routes, components=components, event_hooks=event_hooks)
async_app = ASyncApp(routes=routes, components=components, event_hooks=event_hooks)


@pytest.fixture
def puppy():
    return {"id": 1, "name": "canna"}


@pytest.fixture
def another_puppy():
    return {"id": 2, "name": "puppito"}


@pytest.fixture(params=[app, async_app])
def client(request):
    with database_component.database:
        database_component.database.create_tables([PuppyModel])
    yield TestClient(request.param)
    with database_component.database:
        database_component.database.drop_tables([PuppyModel])


class TestCasePeeweeCRUD:
    def test_create(self, client, puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == [created_puppy]

    def test_retrieve(self, client, puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Retrieve same record
        response = client.get("/puppy/{}".format(created_puppy["id"]))
        assert response.status_code == 200
        assert response.json() == created_puppy

    def test_retrieve_not_found(self, client):
        # retrieve wrong record
        response = client.get("/puppy/43/")
        assert response.status_code == 404

    def test_update(self, client, puppy, another_puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Update record
        response = client.put("/puppy/{}/".format(created_puppy["id"]), json=another_puppy)
        assert response.status_code == 200
        updated_puppy = response.json()
        assert updated_puppy["name"] == "puppito"

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == [updated_puppy]

    def test_update_without_modifying_id(self, client, puppy, another_puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Update record
        response = client.put("/puppy/{}/".format(created_puppy["id"]), json={"name": "puppito"})
        assert response.status_code == 200
        updated_puppy = response.json()
        assert updated_puppy["name"] == "puppito"

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == [{"id": 1, "name": "puppito"}]

    def test_update_not_found(self, client, puppy):
        # Retrieve wrong record
        response = client.put("/puppy/43/", json=puppy)
        assert response.status_code == 404

    def test_delete(self, client, puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Retrieve same record
        response = client.get("/puppy/{}/".format(created_puppy["id"]))
        assert response.status_code == 200
        assert response.json() == created_puppy

        # Delete record
        response = client.delete("/puppy/{}/".format(created_puppy["id"]))
        assert response.status_code == 204

        # Retrieve deleted record
        response = client.get("/puppy/{}".format(created_puppy["id"]))
        assert response.status_code == 404

    def test_delete_not_found(self, client, puppy):
        # Delete wrong record
        response = client.delete("/puppy/43/", json=puppy)
        assert response.status_code == 404

    def test_list(self, client, puppy, another_puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Successfully create another new record
        response = client.post("/puppy/", json=another_puppy)
        assert response.status_code == 201
        created_second_puppy = response.json()
        assert created_second_puppy["name"] == "puppito"

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == [created_puppy, created_second_puppy]

    def test_list_filter(self, client, puppy, another_puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # Successfully create another new record
        response = client.post("/puppy/", json=another_puppy)
        assert response.status_code == 201
        created_second_puppy = response.json()
        assert created_second_puppy["name"] == "puppito"

        # List all the existing records
        response = client.get("/puppy/", params={"name": "canna"})
        assert response.status_code == 200
        assert response.json()["data"] == [created_puppy]

    def test_drop(self, client, puppy):
        # Successfully create a new record
        response = client.post("/puppy/", json=puppy)
        assert response.status_code == 201
        created_puppy = response.json()
        assert created_puppy["name"] == "canna"

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == [created_puppy]

        # Drop collection
        response = client.delete("/puppy/", json=[puppy])
        assert response.status_code == 204
        assert response.json() == {"deleted": 1}

        # List all the existing records
        response = client.get("/puppy/")
        assert response.status_code == 200
        assert response.json()["data"] == []
