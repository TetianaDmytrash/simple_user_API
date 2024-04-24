"""
    simple flask proj 'userAPI'
"""
import datetime
import enum
import uuid

from flask import Flask, jsonify, request
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields

from flask_sqlalchemy import SQLAlchemy

server = Flask(__name__)

class APIConfig:
    API_TITLE = "SIMPLE USER API"
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

userAPI = Blueprint("user", "user", url_prefix="", description="SIMPLE USER API")

userExample = [
    {
        "id": uuid.UUID("5d13b1f4-5df8-44b1-9731-6ea798d30d73"),
        "username": "Rysik",
        "firstName": "Ruslan",
        "lastName": "ArGrah",
        "email": "darkAngel@gmail.com",
        "password": "11q2w33e",
        "summary": "who not?",
        "created": datetime.datetime.now(datetime.timezone.utc),
        "completed": False
    }
]


class UserTable(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    username = db.Column(db.String(10), nullable=False)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text(), nullable=False)
    created = db.Column(db.DateTime(), server_default=db.func.now())
    completed = db.Column(db.Boolean())

    def __repr__(self):
        return self.username

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


class UpdateUser(Schema):
    firstName = fields.String()
    lastName = fields.String()
    email = fields.String()
    completed = fields.Bool()


class CreateUser(UpdateUser):
    username = fields.String()
    password = fields.String()
    summary = fields.String()


class User(CreateUser):
    id = fields.UUID()
    created = fields.DateTime()


class ListUsers(Schema):
    users = fields.List(fields.Nested(User))


class SortByEnum(enum.Enum):
    user = "user"
    created = "created"


class SortDirectionEnum(enum.Enum):
    asc = "asc"
    desc = "desc"


class ListUsersParameters(Schema):
    order_by = fields.Enum(SortByEnum, load_default=SortByEnum.created)
    order = fields.Enum(SortDirectionEnum, load_default=SortDirectionEnum.asc)


@userAPI.route("/users", methods=["GET"])
# @userAPI.arguments(ListUsersParameters, location="query")
# @userAPI.response(status_code=200, schema=ListUsers)
def list_of_all_created_users():
    users = UserTable.get_all()

    serializer = User(many=True)
    data = serializer.dump(users)

    return jsonify(
        data
    ), 200


@userAPI.route("/user", methods=["POST"])
@userAPI.arguments(CreateUser)
@userAPI.response(status_code=201, schema=User)
def create_user(user):
    data = request.get_json()
    if not (2 <= len(data.get("username")) <= 10):
        return jsonify(
            {"message": "Username has invalid length."}
        ), 400
    for i in "!@#$%^&*()_+-=[]{}|;:,.<>?/~":
        if i in data.get("username"):
            return jsonify(
                {"message": "Username has unacceptable symbols."}
            ), 400

    if type(data.get("username")) == int or type(data.get("username")) == bool:
        return jsonify(
            {"message": "Username has invalid type."}
        ), 400

    new_user = UserTable(
        id=str(uuid.uuid4()),
        username=data.get("username"),
        firstName=data.get("firstName"),
        lastName=data.get("lastName"),
        email=data.get("email"),
        password=data.get("password"),
        summary=data.get("summary"),
        completed=False
    )

    new_user.save()

    serializer = User()
    data = serializer.dump(new_user)

    return jsonify(
        {
            "data": data,
            "message": "success create user"
        }
    ), 201

# class UserCollection(MethodView):
#     @userAPI.route("/users")
#     # @userAPI.arguments(ListUsersParameters, location="query")
#     # @userAPI.response(status_code=200, schema=ListUsers)
#     def get(self):
#         users = UserTable.get_all()
#
#         serializer = User(many=True)
#         data = serializer.dump(users)
#
#         return jsonify(
#             data
#         ), 200
#
#     @userAPI.route("/user")
#     @userAPI.arguments(CreateUser)
#     @userAPI.response(status_code=201, schema=User)
#     def post(self, user):
#         data = request.get_json()
#
#         new_user = UserTable(
#             id=str(uuid.uuid4()),
#             username=data.get("username"),
#             firstName=data.get("firstName"),
#             lastName=data.get("lastName"),
#             email=data.get("email"),
#             password=data.get("password"),
#             summary=data.get("summary"),
#             completed=False
#         )
#
#         new_user.save()
#
#         serializer = User()
#         data = serializer.dump(new_user)
#
#         return jsonify(
#             data
#         ), 201


@userAPI.route("/user/<uuid:user_id>")
class ToDoUser(MethodView):

    @userAPI.response(status_code=200, schema=User)
    def get(self, user_id):
        user = UserTable.get_by_id(str(user_id))

        serializer = User()

        data = serializer.dump(user)

        return jsonify(
            data
        ), 200

    @userAPI.arguments(UpdateUser)
    @userAPI.response(status_code=200, schema=User)
    def put(self, payload, user_id):
        user_to_update = UserTable.get_by_id(str(user_id))

        user_to_update.firstName = payload["firstName"]
        user_to_update.lastName = payload["lastName"]
        user_to_update.email = payload["email"]
        user_to_update.completed = payload["completed"]

        db.session.commit()
        serializer = User()
        user_data = serializer.dump(user_to_update)

        return jsonify(
            user_data
        ), 200

    @userAPI.response(status_code=204)
    def delete(self, user_id):
        user_to_delete = UserTable.get_by_id(str(user_id))

        user_to_delete.delete()

        return jsonify(
            {"message": "Deleted"}
        ), 204


@userAPI.errorhandler(404)
def not_found(error):
    return jsonify(
        {"message": "Resource not found"}
    ), 404


@userAPI.errorhandler(500)
def internal_server(error):
    return jsonify(
        {"message": "There is a problem"}
    ), 500


api.register_blueprint(userAPI)


if __name__ == '__main__':
    with server.app_context():
        db.create_all()
    server.run()
