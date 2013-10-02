# -*- coding: UTF-8 -*-
import sqlalchemy as sa

from yawf import constants, WorkFlowEngine
from yawf.utils import do_commit
from yawf.exceptions import (WorkFlowRefused, WorkFlowDelayed,
                             WorkFlowProcessing)


_DBModel = WorkFlowEngine.instance.db.Model
_NodeModel = WorkFlowEngine.instance.node_model


class WorkFlow(_DBModel):

    __tablename__ = 'TB_WORK_FLOW'

    id = sa.Column(sa.Integer, primary_key=True)
    tag = sa.Column(sa.String(32), nullable=False)
    annotation = sa.Column(sa.String(64))
    status = sa.Column(sa.Integer, default=constants.WORK_FLOW_PROCESSING)
    failed = sa.Column(sa.Boolean, default=False)
    root_node_id = sa.Column(sa.Integer,
                             sa.ForeignKey(
                                 _NodeModel.__tablename__ + ".id"))
    root_node = sa.orm.relationship(_NodeModel,
                                    primaryjoin=_NodeModel.__name__ +
                                    ".id==WorkFlow.root_node_id")
    current_node_id = sa.Column(sa.Integer,
                                sa.ForeignKey(_NodeModel.__tablename__ +
                                              ".id"))
    current_node = sa.orm.relationship(_NodeModel,
                                       primaryjoin=_NodeModel.__name__ +
                                       ".id==WorkFlow.current_node_id")
    token = sa.Column(sa.String(32))

    def start(self):
        """
        start the work flow
        """
        self.root_node.approve()

    def retry(self, last_operated_node):
        """
        test if all the nodes are approved, if they are, execute the nodes from
        LEAF to ROOT

        :raise: WorkFlowRefused when the node flow has been refused
        :raise: WorkFlowDelayed when there exists node that hasn't been
        approved
        """
        if self.status == constants.WORK_FLOW_REFUSED:
            raise WorkFlowRefused()
        # then we test if all the (indirect) depenecies of ROOT are met
        unmet_node = self._find_next_unmet_node(self.root_node)
        if unmet_node:
            last_operated_node.on_delayed(unmet_node)
            self.current_node = unmet_node
            do_commit(self)
            raise WorkFlowDelayed(unmet_node,
                                  "node %s is not met" % unicode(unmet_node))
        self.status = constants.WORK_FLOW_APPROVED
        do_commit(self)

        # execute all the nodes
        try:
            self.root_node.execute()
            self.failed = False
            self.status = constants.WORK_FLOW_EXECUTED
            do_commit(self)
        except:
            self.failed = True
            do_commit(self)
            raise

    def _find_next_unmet_node(self, node):
        """
        find the next unapproved node (note, if the node is waiting for
        approvement, it will not be returned)

        :param node: search from it
        """
        if not node.approved:
            return node

        for dep_node in node.dependencies:
            unmet_node = self._find_next_unmet_node(dep_node)
            if unmet_node:
                return unmet_node

    def refuse(self, caused_by):
        """
        :param caused_by: upon which node, the task flow is refused
        """
        self.status = constants.WORK_FLOW_REFUSED
        do_commit(self)
        self._refuse_tree(self.root_node, caused_by)

    def _refuse_tree(self, node, caused_by):
        """
        refuse the node tree roote by 'node'

        :param node: the node tree's root
        :param caused_by: the node refused directly
        """
        node.on_refused(node.id == caused_by.id)
        for t in node.dependencies:
            self._refuse_tree(t, caused_by)

    def execute(self):
        """
        execute the work flow
        you must guarantee each work is a transaction

        :raise WorkFlowRefused: if task flow is refused
        :raise WorkFlowProcessing: if task flow is processing
        :raise Exception: any exceptions raised when executing tasks
        """
        if self.status == constants.WORK_FLOW_REFUSED:
            raise WorkFlowRefused()
        elif self.status == constants.WORK_FLOW_PROCESSING:
            raise WorkFlowProcessing()
        try:
            self.root_node.execute()
            self.failed = False
            self.status == constants.WORK_FLOW_EXECUTED
            do_commit(self)
        except:
            self.failed = True
            do_commit(self)
            raise

    def bind(self, token):
        self.token = token
        do_commit(self)
