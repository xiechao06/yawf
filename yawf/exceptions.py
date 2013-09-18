# -*- coding: UTF-8 -*-

class WorkFlowDelayed(Exception):

    def __init__(self, node, message=""):
        super(WorkFlowDelayed, self).__init__(message)
        self.node = node

class WorkFlowRefused(Exception):
    pass

class WorkFlowProcessing(Exception):
    pass

class NodeAlreadyApproved(Exception):
    pass

class PolicyAlreadyRegistered(Exception):
    pass
