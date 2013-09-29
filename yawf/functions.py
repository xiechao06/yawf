# -*- coding: UTF-8 -*-


import yawf
from yawf.utils import do_commit

def register_policy(policy_cls):
    """
    register a policy

    :raise yawf.exceptions.PolicyAlreadyRegistered: if policy already registered
    :param policy_cls: policy class
    :type policy_cls: yawf.Policy
    """
    yawf.WorkFlowEngine.instance.register_policy(policy_cls)

def new_work_flow(tag, node_creator, tag_creator=None, annotation=None, token=None):
    """
    create a work flow

    :param tag: tag of the work flow
    :param node_creator: a function to create root node, its argument is "work_flow"
    :param tag_creator: a function to create tag, its argument is "work_flow"
    :param annotation: annotation of the work flow
    :param token: token of the work flow
    """
    work_flow = do_commit(yawf.models.WorkFlow(tag=tag, annotation=annotation, token=token))
    work_flow.root_node = do_commit(node_creator(work_flow))
    work_flow.root_node.tag = tag_creator and tag_creator(work_flow) 
    return do_commit(work_flow)

def token_bound(tag, token):
    """
    test if token is bound by any processing work flow

    :param tag: work flow's tag
    :param token: work flow's token
    
    :return: a processing work flow with given tag and token or None
    """
    from sqlalchemy import and_
    model = yawf.models.WorkFlow
    return model.query.filter(and_(model.tag==tag, model.token==token, model.status==yawf.constants.WORK_FLOW_PROCESSING)).first()
