# -*- coding: UTF-8 -*-
import types

def do_commit(obj, action="add"):
    from yawf.work_flow_engine import WorkFlowEngine
    db = WorkFlowEngine.instance.db

    if action == "add":
        if isinstance(obj, types.ListType) or isinstance(obj, types.TupleType):
            db.session.add_all(obj)
        else:
            db.session.add(obj)
    elif action == "delete":
        db.session.delete(obj)
    db.session.commit()
    return obj
