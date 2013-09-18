# -*- coding: UTF-8 -*-
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.exc import NoResultFound

import yawf
import yawf.exceptions
import yawf.constants
from yawf.utils import do_commit

class NodeMixin(object):

    id = sa.Column(sa.Integer, primary_key=True) 
    @declared_attr
    def work_flow_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('TB_WORK_FLOW.id', use_alter=True, name="fk_work_flow_id"))

    @declared_attr
    def work_flow(self):
        return sa.orm.relationship('WorkFlow', primaryjoin='WorkFlow.id=='+self.__name__+".work_flow_id")

    name = sa.Column(sa.String(64))
    approved = sa.Column(sa.Boolean, default=False)
    failed = sa.Column(sa.Boolean, default=False)
    create_time = sa.Column(sa.DateTime, default=datetime.now)
    handle_time = sa.Column(sa.DateTime)
    policy_name = sa.Column(sa.String(32))
    tag = sa.Column(sa.String(32))

    @property
    def policy(self):
        return yawf.WorkFlowEngine.instance.get_policy(self.policy_name)(self)

    def on_delayed(self, unmet_node):
        """
        invoked when the node flow is delayed due to a node that hasn't been approved,
        it's a good place to put some logic like informing the handler of the node
 
        :param unmet_node: the node wait to be approved
        :type unmet_node: lite_node_flow.Work
        """
        return self.policy.on_delayed(unmet_node)

    def on_approved(self):
        return self.policy.on_approved()

    def on_refused(self, caused_by_me):
        return self.policy.on_refused(caused_by_me)

    def after_executed(self):
        return self.policy.after_executed()

    def execute(self):
        return self.policy.execute()

    @property
    def dependencies(self):
        ret = []
        from yawf.models import WorkFlow
        for policy, node_kwargs in self.policy.dependencies:
            try:
                node = self.query.filter(yawf.WorkFlowEngine.instance.node_model.work_flow_id==self.work_flow_id).filter(self.__class__.policy_name==policy).one()
            except NoResultFound:
                node = self.__class__(work_flow=self.work_flow, **node_kwargs)
                do_commit(node)
            ret.append(node)
        return ret

    def approve(self):
        """
        approve the node, and retry the whole work flow to test if it is done

        :raise yawf.exceptions.NodeAlreadyApproved: if node already approved
        """
        if self.approved:
            raise yawf.exceptions.NodeAlreadyApproved()
        self.approved = True
        self.handle_time = datetime.now()
        do_commit(self)
        self.on_approved()
        self.work_flow.retry(self)

    def refuse(self):
        """
        refuse the node, and the whole work flow

        :raise yawf.exceptions.WorkFlowRefused: if work flow already refused
        """
        if self.work_flow.status == yawf.constants.WORK_FLOW_REFUSED: 
            raise yawf.exceptions.WorkFlowRefused()
        self.approved = False
        self.handle_time = datetime.now()
        do_commit(self)
        self.work_flow.refuse(self)


    def __unicode__(self):
        return '<Node %s>' % self.policy_name

