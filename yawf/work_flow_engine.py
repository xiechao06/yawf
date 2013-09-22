# -*- coding: UTF-8 -*-
import yawf
from yawf.utils import do_commit
import md5

class WorkFlowEngine(object):

    instance = None

    def __init__(self, db, node_model):
        self.db = db
        self.node_model = node_model
        self._registered_policy_cls_map = {}
        WorkFlowEngine.instance = self

    def register_policy(self, policy_cls):
        """
        register a policy

        :raise: yawf.exceptions.PolicyAlreadyRegistered if policy already registered
        :param policy_cls: policy class
        :type policy_cls: yawf.Policy
        """
        if policy_cls.__name__ in self._registered_policy_cls_map:
            raise yawf.exceptions.PolicyAlreadyRegistered()

        self._registered_policy_cls_map[policy_cls.__name__] = policy_cls

    def get_policy(self, policy_name):
        '''
        get a registered policy

        :return: a policy with given name
        '''
        return self._registered_policy_cls_map[policy_name]

