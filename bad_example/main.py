from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from flask_smorest import Api, Blueprint

app = Flask(__name__)

class APIConfig:
    API_TITLE = "PETSTORE API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_UI_URL = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone"


app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost/simple_API"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_object(APIConfig)
db = SQLAlchemy(app)
api = Api(app)

class Recipe(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return self.name

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

class RecipeSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()

recipe_blp = Blueprint(
    "recipes", "recipes", url_prefix="/recipes", description="Operations on recipes"
)

@recipe_blp.route("/recipes", methods=["GET"])
#@recipe_blp.response(RecipeSchema(many=True))
def get_all_recipes():
    recipes = Recipe.get_all()

    serializer = RecipeSchema(many=True)
    data = serializer.dump(recipes)

    return jsonify(
        data
    )

@recipe_blp.route("/recipes", methods=["POST"])
@recipe_blp.arguments(RecipeSchema)
def create_a_recipe():
    data = request.get_json()

    new_recipe = Recipe(
        name=data.get("name"),
        description=data.get("description")
    )

    new_recipe.save()

    serializer = RecipeSchema()
    data = serializer.dump(new_recipe)

    return jsonify(
        data
    ), 201

@recipe_blp.route("/recipe/<int:id>", methods=["GET"])
# @recipe_blp.response(RecipeSchema)
def get_recipe(id):
    recipe = Recipe.get_by_id(id)

    serializer = RecipeSchema()

    data = serializer.dump(recipe)

    return jsonify(
        data
    ), 200

@recipe_blp.route("/recipe/<int:id>", methods=["PUT"])
@recipe_blp.arguments(RecipeSchema)
# @recipe_blp.response(RecipeSchema)
def update_recipe(id):
    recipe_to_update = Recipe.get_by_id(id)

    data = request.get_json()
    recipe_to_update.name = data.get("name")
    recipe_to_update.description = data.get("description")

    db.session.commit()
    serializer = RecipeSchema()
    recipe_data = serializer.dump(recipe_to_update)

    return jsonify(
        recipe_data
    ), 200

@recipe_blp.route("/recipe/<int:id>", methods=["PUT"])
# @recipe_blp.response(code=204)
def delete_recipe(id):
    recipe_to_delete = Recipe.get_by_id(id)

    recipe_to_delete.delete()

    return jsonify(
        {"message": "Deleted"}
    ), 204

@recipe_blp.errorhandler(404)
def not_found(error):
    return jsonify(
        {"message": "Resource not found"}
    ), 404


@recipe_blp.errorhandler(500)
def internal_server(error):
    return jsonify(
        {"message": "There is a problem"}
    ), 500

api.register_blueprint(recipe_blp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
