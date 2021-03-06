#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import json
from py.test import raises
from mock import patch
import yawf
from yawf.test.base_test import BaseTest


class Test(BaseTest):

    def test(self):
        self._test_single_node()
        self._test_multiple_node()
        self._test_execution()
        self._test_binding()
        self._test_web_services()

    def _test_single_node(self):

        yawf.clear_polices()

        class FooPolicy(yawf.Policy):
            pass

        yawf.register_policy(FooPolicy)

        _NodeModel = yawf.WorkFlowEngine.instance.node_model

        with patch.object(FooPolicy, "__call__") as mock_method1:
            with patch.object(FooPolicy, "on_approved") as mock_method2:
                with patch.object(FooPolicy, "after_executed") as mock_method3:
                    work_flow = yawf.new_work_flow('foo work flow',
                                                   lambda work_flow:
                                                   _NodeModel(
                                                       work_flow=work_flow,
                                                       name='foo task',
                                                       policy_name='FooPolicy')
                                                   )
                    work_flow.start()
                    mock_method1.assert_called_once_with()
                    mock_method2.assert_called_once_with()
                    mock_method3.assert_called_once_with()
                    assert work_flow.status == yawf.constants.WORK_FLOW_EXECUTED

        with patch.object(FooPolicy, "__call__") as mock_method1:
            with patch.object(FooPolicy, "on_approved") as mock_method2:
                with patch.object(FooPolicy, "after_executed") as mock_method3:
                    with patch.object(FooPolicy, "on_refused") as mock_method4:
                        work_flow = yawf.new_work_flow('foo work flow',
                                                       lambda work_flow:
                                                       _NodeModel(
                                                           work_flow=work_flow,
                                                           name='foo task',
                                                           policy_name='FooPolicy')
                                                       )
                        work_flow.root_node.refuse()
                        assert mock_method1.call_count == 0
                        assert mock_method2.call_count == 0
                        assert mock_method3.call_count == 0
                        mock_method4.assert_called_once_with(True)
                        assert work_flow.status == yawf.constants.WORK_FLOW_REFUSED

        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='foo task', policy_name='FooPolicy'))
        work_flow.start()
        raises(yawf.exceptions.NodeAlreadyApproved,
               work_flow.root_node.approve)

    def _test_multiple_node(self):

        yawf.clear_polices()

        class A(yawf.Policy):
            @property
            def dependencies(self):
                return [('B', {'name': 'B'}), ('C', {'name': 'C'})]

        class B(yawf.Policy):
            pass

        class C(yawf.Policy):

            @property
            def dependencies(self):
                return [('D', {'name': 'D'})]

        class D(yawf.Policy):
            pass

        yawf.register_policy(A)
        yawf.register_policy(B)
        yawf.register_policy(C)
        yawf.register_policy(D)

        with patch.object(A, "__call__") as call_a:
            with patch.object(B, "__call__") as call_b:
                with patch.object(C, "__call__") as call_c:
                    with patch.object(D, "__call__") as call_d:
                        work_flow = yawf.new_work_flow('foo work flow',
                                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='A', policy_name='A'))
                        e_info = raises(yawf.exceptions.WorkFlowDelayed, work_flow.start)
                        assert work_flow.root_node.approved
                        delayed_node = e_info.value.node
                        assert not delayed_node.approved

                        e_info = raises(yawf.exceptions.WorkFlowDelayed, delayed_node.approve)
                        assert delayed_node.approved
                        delayed_node = e_info.value.node
                        assert not delayed_node.approved
                        assert delayed_node.id == work_flow.current_node_id

                        e_info = raises(yawf.exceptions.WorkFlowDelayed, delayed_node.approve)
                        assert delayed_node.approved
                        delayed_node = e_info.value.node
                        assert not delayed_node.approved

                        delayed_node.approve()
                        call_a.assert_called_once_with()
                        call_b.assert_called_once_with()
                        call_c.assert_called_once_with()
                        call_d.assert_called_once_with()

                        assert not delayed_node.failed
                        assert not work_flow.failed

        ## test refused
        with patch.object(B, "on_refused") as mock_method:
            work_flow = yawf.new_work_flow('foo work flow',
                                           lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='A', policy_name='A'))
            try:
                work_flow.start()
            except yawf.exceptions.WorkFlowDelayed, e:
                delayed_node = e.node
            delayed_node.refuse()
            assert work_flow.status == yawf.constants.WORK_FLOW_REFUSED
            mock_method.assert_called_once_with(True)
            raises(yawf.exceptions.WorkFlowRefused, delayed_node.approve)

        # test approve twice
        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='A', policy_name='A'))
        try:
            work_flow.start()
        except yawf.exceptions.WorkFlowDelayed:
            pass
        raises(yawf.exceptions.NodeAlreadyApproved, work_flow.root_node.approve)

    def _test_execution(self):

        yawf.clear_polices()

        class E(yawf.Policy):

            def __call__(self):
                raise RuntimeError()

            @property
            def dependencies(self):
                return [('F', {
                    'name': 'F',
                })]

        class F(yawf.Policy):
            pass

        yawf.register_policy(E)
        yawf.register_policy(F)

        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='E', policy_name='E'))
        try:
            work_flow.start()
        except yawf.exceptions.WorkFlowDelayed, e:
            delayed_node = e.node
        raises(RuntimeError, delayed_node.approve)

        assert work_flow.failed
        assert not delayed_node.failed
        assert work_flow.root_node.failed
        assert work_flow.status == yawf.constants.WORK_FLOW_APPROVED

        raises(RuntimeError, work_flow.execute)

        assert work_flow.failed
        assert not delayed_node.failed
        assert work_flow.root_node.failed
        assert work_flow.status == yawf.constants.WORK_FLOW_APPROVED

        class E_(yawf.Policy):

            @property
            def dependencies(self):
                return [('F', {
                    'name': 'F',
                })]
        yawf.register_policy(E_)
        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='E_', policy_name='E_'))
        try:
            work_flow.start()
        except yawf.exceptions.WorkFlowDelayed, e:
            delayed_node = e.node

        delayed_node.approve()
        assert work_flow.status == yawf.constants.WORK_FLOW_EXECUTED

    def _test_binding(self):

        yawf.clear_polices()

        class G(yawf.Policy):
            pass

        yawf.register_policy(G)

        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: yawf.WorkFlowEngine.instance.node_model(work_flow=work_flow, name='G', policy_name='G'),
                                       token='foo')

        assert yawf.token_bound('foo work flow', 'foo')

        work_flow.start()
        assert not yawf.token_bound('foo work flow', 'foo')

    def _test_web_services(self):

        yawf.clear_polices()

        class FooPolicy(yawf.Policy):
            pass

        yawf.register_policy(FooPolicy)
        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: self.node_model(
                                           work_flow=work_flow,
                                           name='foo task',
                                           policy_name='FooPolicy'))
        work_flow.start()

        with self.app.test_client() as c:
            rv = c.get('/__flask_yawf__/node/' + str(work_flow.root_node.id))
            assert rv.status_code == 200
            d = json.loads(rv.data)
            assert d['id'] == work_flow.root_node.id
            assert d['work_flow_id'] == work_flow.id
            assert d['name'] == work_flow.root_node.name
            assert not d['failed']
            assert d['policy_name'] == 'FooPolicy'

        class A(yawf.Policy):

            @property
            def dependencies(self):
                return [('B', {'name': 'B'})]

        class B(yawf.Policy):

            pass

        yawf.register_policies(A, B)
        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: self.node_model(
                                           work_flow=work_flow,
                                           name='foo task',
                                           policy_name='FooPolicy'))
        work_flow.start()
        with patch.object(B, '__call__') as mock_method1:
            with self.app.test_client() as c:
                rv = c.put('/__flask_yawf__/node/%d?action=approve' %
                           work_flow.root_node.id)
                assert rv.status_code == 200

                node = self.node_model.query.get(work_flow.root_node.id)
                assert node.approved
                assert mock_method1.call_count == 0

        work_flow = yawf.new_work_flow('foo work flow',
                                       lambda work_flow: self.node_model(
                                           work_flow=work_flow,
                                           name='foo task',
                                           policy_name='FooPolicy'))
        work_flow.start()
        with patch.object(B, '__call__') as mock_method1:
            with patch.object(B, 'on_refused') as mock_method2:
                with patch.object(B, 'on_refused') as mock_method2:
                    rv = c.put('/__flask_yawf__/node/%d?action=refuse' %
                               work_flow.root_node.id)
                assert rv.status_code == 200

                root_node = self.node_model.query.get(work_flow.root_node.id)
                assert root_node.approved
                for node in root_node.dependencies:
                    assert not node.approved
                assert mock_method1.call_count == 0
                assert mock_method2.called_once_with(True)
                assert mock_method1.called_once_with(False)


if __name__ == '__main__':
    Test().run_plainly()
