import tempfile
import os
import types

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from yawf.ext.flask import FlaskYawf


class BaseTest(object):

    def setup(self):
        self.db_fd, self.db_fname = tempfile.mkstemp()
        os.close(self.db_fd)
        dbstr = "sqlite:///" + self.db_fname + ".db"

        self.app = Flask(__name__)
        self.app.config['DEBUG'] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = dbstr
        self.app.config["CSRF_ENABLED"] = False
        self.app.config["SECRET_KEY"] = "D8123;d;"
        self.db = SQLAlchemy(self.app)

        import yawf.node_mixin

        class Node(yawf.node_mixin.NodeMixin, self.db.Model):
            __tablename__ = 'TB_NODE'
        self.node_model = Node
        FlaskYawf(self.app, self.db, self.node_model)
        from yawf.models import WorkFlow
        self.db.create_all()

    def teardown(self):
        self.db.drop_all()
        os.unlink(self.db_fname)

    def run_plainly(self, tests=None):
        self.setup()
        for k, v in self.__class__.__dict__.items():
            if k.startswith("test") and isinstance(v, types.FunctionType):
                if not tests or (k in tests):
                    v(self)
        self.teardown()
