#! /usr/bin/env python
import types

from basemain import app
from database import sa_db, init_db
from models import Group, User
from yawf.utils import do_commit

sa_db.drop_all()
init_db()

customers = do_commit(Group(name='Customers'))
clerks = do_commit(Group(name='Clerks'))
do_commit(User(username='Tom', group=customers))
do_commit(User(username='Jerry', group=clerks))
