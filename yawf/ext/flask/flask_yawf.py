# -*- coding: UTF-8 -*-
import json

from wtforms import TextField, validators
from flask import Blueprint, request
from flask.ext.wtf import Form

from yawf import WorkFlowEngine


class FlaskYawf(object):

    __blueprint__ = '__flask_yawf__'

    def __init__(self, app, db, node_model):
        self.app = app
        WorkFlowEngine(db, node_model)
        self.blueprint = Blueprint(self.__blueprint__, __name__,
                                   static_folder="static",
                                   template_folder="templates")
        self.blueprint.add_url_rule(self.node_view_url,
                                    self.node_view_endpoint,
                                    self.node_view, methods=['GET', 'PUT'])
        app.register_blueprint(self.blueprint,
                               url_prefix='/' + self.__blueprint__)

    @property
    def node_view_url(self):
        return '/node/<id_>'

    @property
    def node_view_endpoint(self):
        return 'node'

    def node_dict(self, node):
        '''
        convert node to a dict
        '''
        return dict(id=node.id,
                    work_flow_id=node.work_flow_id,
                    name=node.name,
                    approved=node.approved,
                    failed=node.failed,
                    create_time=str(node.create_time),
                    handle_time=str(node.handle_time or ''),
                    policy_name=node.policy_name,
                    tag=node.tag)

    def node_view(self, id_):

        class _Form(Form):
            action = TextField('action',
                               validators=[
                                   validators.AnyOf('approve', 'refuse')
                               ])

        node_model = WorkFlowEngine.instance.node_model
        node = node_model.query.get_or_404(id_)
        if request.method == 'GET':
            return json.dumps(self.node_dict(node))
        else:
            form = _Form(request.args)
            if form.validate():
                if form.action == 'approve':
                    try:
                        node.approve()
                    except Exception, e:
                        return str(e), 403
                else:
                    try:
                        node.refuse()
                    except Exception, e:
                        return str(e), 403
        return ""
