"""
    simple flask proj 'todo'
"""
import datetime
import enum
import uuid

from flask import Flask, abort, jsonify, request
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields

from flask_sqlalchemy import SQLAlchemy

server = Flask(__name__)

class APIConfig:
    API_TITLE = "TODO API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_UI_URL = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone"


server.config.from_object(APIConfig)
server.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost/simple_API"
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(server)
api = Api(server)

todo = Blueprint("todo", "todo", url_prefix="", description="TODO API")

tasks = [
    {
        "id": uuid.UUID("5d13b1f4-5df8-44b1-9731-6ea798d30d73"),
        "created": datetime.datetime.now(datetime.timezone.utc),
        "completed": False,
        "task": "create flask API tutorial",
        "description": "create",
    }
]


class TaskT(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    created = db.Column(db.DateTime(), server_default=db.func.now())
    completed = db.Column(db.Boolean())
    description = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return self.task

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class CreateTask(Schema):
    task = fields.String()
    description = fields.String()


class UpdateTask(CreateTask):
    completed = fields.Bool()


class Task(UpdateTask):
    id = fields.UUID()
    created = fields.DateTime()


class ListTasks(Schema):
    tasks = fields.List(fields.Nested(Task))

class SortByEnum(enum.Enum):
    task = "task"
    created = "created"


class SortDirectionEnum(enum.Enum):
    asc = "asc"
    desc = "desc"


class ListTasksParameters(Schema):
    order_by = fields.Enum(SortByEnum, load_default=SortByEnum.created)
    order = fields.Enum(SortDirectionEnum, load_default=SortDirectionEnum.asc)


@todo.route("/tasks")
class TodoCollection(MethodView):

    # @todo.arguments(ListTasksParameters, location="query")
    # @todo.response(status_code=200, schema=ListTasks)
    def get(self):
        recipes = TaskT.get_all()

        serializer = Task(many=True)
        data = serializer.dump(recipes)

        return jsonify(
            data
        ), 200

    @todo.arguments(CreateTask)
    @todo.response(status_code=201, schema=Task)
    def post(self, task):
        data = request.get_json()

        new_recipe = TaskT(
            id=str(uuid.uuid4()),
            task=data.get("task"),
            completed=False,
            description=data.get("description")
        )

        new_recipe.save()

        serializer = Task()
        data = serializer.dump(new_recipe)

        return jsonify(
            data
        ), 201


@todo.route("/task/<uuid:task_id>")
class ToDoTask(MethodView):

    @todo.response(status_code=200, schema=Task)
    def get(self, task_id):
        recipe = TaskT.get_by_id(str(task_id))

        serializer = Task()

        data = serializer.dump(recipe)

        return jsonify(
            data
        ), 200

    @todo.arguments(UpdateTask)
    @todo.response(status_code=200, schema=Task)
    def put(self, payload, task_id):
        recipe_to_update = TaskT.get_by_id(str(task_id))

        # data = request.get_json()
        recipe_to_update.description = payload["description"]
        recipe_to_update.task = payload["task"]
        recipe_to_update.completed = payload["completed"]

        db.session.commit()
        serializer = Task()
        recipe_data = serializer.dump(recipe_to_update)

        return jsonify(
            recipe_data
        ), 200

    @todo.response(status_code=204)
    def delete(self, task_id):
        recipe_to_delete = TaskT.get_by_id(str(task_id))

        recipe_to_delete.delete()

        return jsonify(
            {"message": "Deleted"}
        ), 204


@todo.errorhandler(404)
def not_found(error):
    return jsonify(
        {"message": "Resource not found"}
    ), 404


@todo.errorhandler(500)
def internal_server(error):
    return jsonify(
        {"message": "There is a problem"}
    ), 500


api.register_blueprint(todo)


if __name__ == '__main__':
    with server.app_context():
        db.create_all()
    server.run()
