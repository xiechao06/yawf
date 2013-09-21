# -*- coding: UTF-8 -*-
from yawf.utils import do_commit
from yawf import constants

class Policy(object):

    def __init__(self, node):
        self.node = node

    @property
    def dependencies(self):
        """
        :return: a list of plicies depentent on, each element is a 2-items tuple, 
        of which the first is a policy's name, the second is a dict used to 
        generate the node, except the 'policy_name' argument
        """
        return []

    @property
    def work_flow(self):
        return self.node.work_flow

    def execute(self):
        """
        execute the policy, all the dependent policy will be executed at first
        """
        for node in self.node.dependencies:
            node.execute()

        if not self.work_flow.status == constants.WORK_FLOW_EXECUTED or self.node.failed:
            try:
                self()
                self.node.failed = False
                do_commit(self.node)
                self.after_executed()
            except:
                self.node.failed = True
                do_commit(self.node)
                raise
    
    def __call__(self):
        """
        put the execution code here if necessary
        """
        pass

    def on_delayed(self, unmet_node):
        """
        invoked when the task flow is delayed due to a task that hasn't been approved,
        it's a good place to put some logic like informing the handler of the task
 
        :param unmet_task: the task wait to be approved
        :type unmet_task: lite_task_flow.Task
        """
        pass

    def on_approved(self):
        """
        invoked when the task is approved
        """
        pass

    def on_refused(self, caused_by_me):
        """
        invoked when the task flow is refused, and the task is submitted and wait for
        approving.

        :param caused_by_me: if the refused task is me
        :type caused_by_me: boolean
        """
        pass

    def after_executed(self):
        """
        this method is invoked when the task is performed
        override this method to perform actions like informing somebody
        """
        pass

    @property
    def annotation(self):
        pass
