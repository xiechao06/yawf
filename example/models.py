# -*- coding: UTF-8 -*-
from flask.ext.login import UserMixin 
import yawf

from basemain import app
from database import sa_db

class User(UserMixin, sa_db.Model):

    __tablename__ = 'TB_USER'
    
    id = sa_db.Column(sa_db.Integer, primary_key=True)
    username = sa_db.Column(sa_db.String(32), nullable=False, unique=True)
    group_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('TB_GROUP.id'))
    group = sa_db.relationship("Group")

    @property
    def is_clerk(self):
        return self.group.name == 'Clerks'

class Group(sa_db.Model):

    __tablename__ = 'TB_GROUP'
    id = sa_db.Column(sa_db.Integer, primary_key=True)
    name = sa_db.Column(sa_db.String(32), nullable=False, unique=True)

from yawf.node_mixin import NodeMixin
from database import sa_db
from sqlalchemy.ext.declarative import declared_attr

class Node(sa_db.Model, NodeMixin):

    __tablename__ = 'TB_NODE'

    @declared_attr
    def handler_group_id(self):
        return sa_db.Column(sa_db.Integer, sa_db.ForeignKey('TB_GROUP.id'))

    @declared_attr
    def handler_group(self):
        return sa_db.relationship('Group')

class Application(sa_db.Model):

    __tablename__ = 'TB_APPLICATION'

    id = sa_db.Column(sa_db.Integer, primary_key=True)
    username = sa_db.Column(sa_db.String(32), nullable=False)
    destination = sa_db.Column(sa_db.String(32), nullable=False)
    contact = sa_db.Column(sa_db.String(32), nullable=False)
    work_flow_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('TB_WORK_FLOW.id'))
    work_flow = sa_db.relationship('WorkFlow')
