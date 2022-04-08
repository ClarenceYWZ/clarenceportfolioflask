from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from graph_flask.config import Config
from flask_security import SQLAlchemySessionUserDatastore, Security
from flask_principal import Principal
from flask_marshmallow import Marshmallow
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session
import os
from flask_cors import CORS
# import msal
# import requests

db = SQLAlchemy()
ma = Marshmallow()

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
mail = Mail()
# requests_session = requests.Session()



def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app, support_credentials=True)
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.secret_key = os.urandom(24)
    db.init_app(app)
    ma.init_app(app)
    sess = Session()

    # ui = FlaskUI(app)
    sess.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Principal(app)
    # api = Api(app)

    from graph_flask.users.routes import users
    # from flask_project.posts.routes import posts
    from graph_flask.main.routes import main
    from graph_flask.agm.routes import agm
    from graph_flask.ap_module.routes import ap_module
    from graph_flask.ar_module.routes import ar_module
    from graph_flask.microsoft.routes import microsoft
    from graph_flask.zoom.routes import zoom
    from graph_flask.printing_postage.routes import printing_postage

    # from flask_project.mcst.routes import mcst
    # from flask_project.temp.routes import temp
    # from flask_project.errors.handlers import errors
    from graph_flask.models import User, Role
    # # from flask_project.copier.routes import copier
    def user_datastore():
        return  SQLAlchemySessionUserDatastore(db, User, Role)
        security = Security(app, user_datastore)



    app.register_blueprint(users)
    app.register_blueprint(microsoft)
    app.register_blueprint(main)
    app.register_blueprint(agm)
    app.register_blueprint(zoom)
    app.register_blueprint(ar_module)
    app.register_blueprint(printing_postage)

    # app.register_blueprint(errors)
    # app.register_blueprint(mcst)
    # app.register_blueprint(temp)

    # app.register_blueprint(copier)

    # app.jinja_env.globals.update(_build_auth_url=_build_auth_url)  # Used in template
    return app
    # return ui





