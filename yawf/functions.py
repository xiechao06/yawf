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

def new_work_flow(annotation, node_creator, tag_creator=None):
    """
    create a work flow

    :param annotation: annotation of the work flow
    :node_creator: a function to create root node, its argument is "work_flow"
    :tag_creator: a function to create tag, its argument is "work_flow"
    """
    work_flow = do_commit(yawf.models.WorkFlow(annotation=annotation))
    work_flow.root_node = do_commit(node_creator(work_flow))
    work_flow.root_node.tag = tag_creator and tag_creator(work_flow) 
    return do_commit(work_flow)
                          
