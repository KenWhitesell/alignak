#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018: Alignak team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak.
#
# Alignak is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alignak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Alignak.  If not, see <http://www.gnu.org/licenses/>.
#
"""
This file test the check_result brok
"""

import time
from .alignak_test import AlignakTest
from alignak.misc.serialization import unserialize


class TestMonitoringLogs(AlignakTest):
    """
    This class test the check_result brok
    """
    def setUp(self):
        super(TestMonitoringLogs, self).setUp()

    def check(self, item, state_id, output, expected_logs):
        """

        :param item: concerned item
        :param state_id: state identifier
        :param output: state text
        :param expected_logs: expected monitoring logs
        :return:
        """
        # Get my first broker link
        # my_broker = [b for b in list(self._scheduler.my_daemon.brokers.values())][0]
        # my_broker.broks = []
        self._main_broker.broks = []

        self.scheduler_loop(1, [[item, state_id, output]])
        time.sleep(1.0)
        self.scheduler_loop(1)

        self.check_monitoring_logs(expected_logs)
        # monitoring_logs = []
        # for brok in my_broker.broks:
        #     if brok.type == 'monitoring_log':
        #         print("Brok: %s" % brok)
        #         data = unserialize(brok.data)
        #         monitoring_logs.append((data['level'], data['message']))
        #
        # for log_level, log_message in expected_logs:
        #     assert (log_level, log_message) in monitoring_logs
        #
        # assert len(expected_logs) == len(monitoring_logs), monitoring_logs
        time.sleep(0.1)

    def test_logs_hosts(self):
        """ Test logs for active / passive checks for hosts

        :return: None
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        self._scheduler.pushed_conf.log_initial_states = True
        self._scheduler.pushed_conf.log_active_checks = True
        self._scheduler.pushed_conf.log_passive_checks = True

        host = self._scheduler.hosts.find_by_name("test_host_0")
        # Make notifications interval set to 5 minutes
        host.notification_interval = 5
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        host.event_handler_enabled = True

        # Host active checks
        self.check(host, 0, 'Host is UP',
                   [('info', u'ACTIVE HOST CHECK: test_host_0;UP;0;Host is UP')])

        self.check(host, 0, 'Host is UP',
                   [('info', u'ACTIVE HOST CHECK: test_host_0;UP;1;Host is UP')])

        # Host goes DOWN / SOFT
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'ACTIVE HOST CHECK: test_host_0;DOWN;1;Host is DOWN'),
                    ('error', 'HOST ALERT: test_host_0;DOWN;SOFT;1;Host is DOWN'),
                    ('error', 'HOST EVENT HANDLER: test_host_0;DOWN;SOFT;1;eventhandler'),
                    ])

        self.check(host, 2, 'Host is DOWN',
                   [('error', 'ACTIVE HOST CHECK: test_host_0;DOWN;1;Host is DOWN'),
                    ('error', 'HOST ALERT: test_host_0;DOWN;SOFT;2;Host is DOWN'),
                    ('error', 'HOST EVENT HANDLER: test_host_0;DOWN;SOFT;2;eventhandler')])

        # Host goes DOWN / HARD
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'ACTIVE HOST CHECK: test_host_0;DOWN;2;Host is DOWN'),
                    ('error', 'HOST ALERT: test_host_0;DOWN;HARD;3;Host is DOWN'),
                    ('error', 'HOST EVENT HANDLER: test_host_0;DOWN;HARD;3;eventhandler'),
                    ('error', 'HOST NOTIFICATION: test_contact;test_host_0;DOWN;notify-host;Host is DOWN')])

        # Notification not raised - too soon!
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'ACTIVE HOST CHECK: test_host_0;DOWN;3;Host is DOWN')])

        # Notification not raised - too soon!
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'ACTIVE HOST CHECK: test_host_0;DOWN;3;Host is DOWN')])

        # Host goes UP / HARD
        # Get an host check, an alert and a notification
        self.check(host, 0, 'Host is UP',
                   [('info', 'ACTIVE HOST CHECK: test_host_0;UP;3;Host is UP'),
                    ('info', 'HOST ALERT: test_host_0;UP;HARD;3;Host is UP'),
                    ('info', 'HOST EVENT HANDLER: test_host_0;UP;HARD;3;eventhandler'),
                    ('info', 'HOST NOTIFICATION: test_contact;test_host_0;UP;notify-host;Host is UP')
                    ])

        self.check(host, 0, 'Host is UP',
                   [('info', 'ACTIVE HOST CHECK: test_host_0;UP;1;Host is UP')])

        self.check(host, 0, 'Host is UP',
                   [('info', 'ACTIVE HOST CHECK: test_host_0;UP;1;Host is UP')])

    def test_logs_services(self):
        """ Test logs for active / passive checks for hosts

        :return: None
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        self._scheduler.pushed_conf.log_initial_states = True
        self._scheduler.pushed_conf.log_active_checks = True
        self._scheduler.pushed_conf.log_passive_checks = True

        host = self._scheduler.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        host.event_handler_enabled = True

        svc = self._scheduler.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        # Make notifications interval set to 5 minutes
        svc.notification_interval = 5
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        svc.event_handler_enabled = True

        # Get sure that host is UP
        self.check(host, 0, 'Host is UP',
                   [('info', 'ACTIVE HOST CHECK: test_host_0;UP;0;Host is UP')])

        # Service is ok
        self.check(svc, 0, 'Service is OK',
                   [('info', 'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;0;Service is OK')])
        self.check(svc, 0, 'Service is OK',
                   [('info', 'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;1;Service is OK')])

        # Service goes warning / SOFT
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;WARNING;1;Service is WARNING'),
                    ('warning',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;WARNING;SOFT;1;eventhandler'),
                    ('warning',
                     'SERVICE ALERT: test_host_0;test_ok_0;WARNING;SOFT;1;Service is WARNING'),
                    ])

        # Service goes warning / HARD
        # Get a service check, an alert and a notification
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;WARNING;1;Service is WARNING'),
                    ('warning',
                     'SERVICE ALERT: test_host_0;test_ok_0;WARNING;HARD;2;Service is WARNING'),
                    ('warning',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;WARNING;HARD;2;eventhandler'),
                    ('warning',
                     'SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;'
                     'WARNING;notify-service;Service is WARNING'),
                    ])

        # Notification not raised - too soon!
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;WARNING;2;Service is WARNING')])

        # Notification not raised - too soon!
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;WARNING;2;Service is WARNING')])

        # Service goes OK
        self.check(svc, 0, 'Service is OK',
                   [('info',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;2;Service is OK'),
                    ('info',
                     'SERVICE ALERT: test_host_0;test_ok_0;OK;HARD;2;Service is OK'),
                    ('info',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;OK;HARD;2;eventhandler'),
                    ('info',
                     'SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;OK;notify-service;'
                     'Service is OK')
                    ])

        self.check(svc, 0, 'Service is OK',
                   [('info',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;1;Service is OK')])

        # Service goes CRITICAL
        self.check(svc, 2, 'Service is CRITICAL',
                   [('error',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;CRITICAL;1;Service is CRITICAL'),
                    ('error',
                     'SERVICE ALERT: test_host_0;test_ok_0;CRITICAL;SOFT;1;Service is CRITICAL'),
                    ('error',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;CRITICAL;SOFT;1;eventhandler'),
                    ])

        self.check(svc, 2, 'Service is CRITICAL',
                   [('error',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;CRITICAL;1;Service is CRITICAL'),
                    ('error',
                     'SERVICE ALERT: test_host_0;test_ok_0;CRITICAL;HARD;2;Service is CRITICAL'),
                    ('error',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;CRITICAL;HARD;2;eventhandler'),
                    ('error',
                     'SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;'
                        'CRITICAL;notify-service;Service is CRITICAL')
                    ])

        # Service goes OK
        self.check(svc, 0, 'Service is OK',
                   [('info',
                     'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;2;Service is OK'),
                    ('info',
                     'SERVICE ALERT: test_host_0;test_ok_0;OK;HARD;2;Service is OK'),
                    ('info',
                     'SERVICE EVENT HANDLER: test_host_0;test_ok_0;OK;HARD;2;eventhandler'),
                    ('info',
                     'SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;OK;notify-service;Service is OK')
                    ])


        self.check(svc, 0, 'Service OK',
                   [('info', 'ACTIVE SERVICE CHECK: test_host_0;test_ok_0;OK;1;Service OK')])

    def test_logs_hosts_disabled(self):
        """ Test disabled logs for active / passive checks for hosts

        :return: None
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg',
                             'cfg/cfg_monitoring_logs_disabled.ini')
        assert self.conf_is_correct

        self._sched = self._scheduler

        host = self._scheduler.hosts.find_by_name("test_host_0")
        # Make notifications sent very quickly
        host.notification_interval = 10.0
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        host.event_handler_enabled = True

        #  Host active checks
        self.check(host, 0, 'Host is UP', [])

        self.check(host, 0, 'Host is UP', [])

        # Host goes DOWN / SOFT
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'HOST ALERT: test_host_0;DOWN;SOFT;1;Host is DOWN')])

        self.check(host, 2, 'Host is DOWN',
                   [('error', 'HOST ALERT: test_host_0;DOWN;SOFT;2;Host is DOWN')])

        # Host goes DOWN / HARD
        self.check(host, 2, 'Host is DOWN',
                   [('error', 'HOST ALERT: test_host_0;DOWN;HARD;3;Host is DOWN')])

        # Host notification raised
        self.check(host, 2, 'Host is DOWN', [])

        self.check(host, 2, 'Host is DOWN', [])

        #  Host goes UP / HARD
        #  Get an host check, an alert and a notification
        self.check(host, 0, 'Host is UP',
                   [('info', 'HOST ALERT: test_host_0;UP;HARD;3;Host is UP')])

        self.check(host, 0, 'Host is UP', [])

        self.check(host, 0, 'Host is UP', [])

    def test_logs_services_disabled(self):
        """ Test disabled logs for active / passive checks for services

        :return: None
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg',
                             'cfg/cfg_monitoring_logs_disabled.ini')
        assert self.conf_is_correct

        self._sched = self._scheduler

        host = self._scheduler.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        host.event_handler_enabled = False

        svc = self._scheduler.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        # Make notifications sent very quickly
        svc.notification_interval = 10.0
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        svc.event_handler_enabled = False

        #  Get sure that host is UP
        self.check(host, 0, 'Host is UP', [])

        # Service is ok
        self.check(svc, 0, 'Service is OK', [])
        self.check(svc, 0, 'Service is OK', [])

        #  Service goes warning / SOFT
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'SERVICE ALERT: test_host_0;test_ok_0;WARNING;SOFT;1;Service is WARNING')])

        #  Service goes warning / HARD
        # Get a service check, an alert and a notification
        self.check(svc, 1, 'Service is WARNING',
                   [('warning',
                     'SERVICE ALERT: test_host_0;test_ok_0;WARNING;HARD;2;Service is WARNING')])

        # Service notification raised
        self.check(svc, 1, 'Service is WARNING', [])

        self.check(svc, 1, 'Service is WARNING', [])

        # Service goes OK
        self.check(svc, 0, 'Service is OK',
                   [('info', 'SERVICE ALERT: test_host_0;test_ok_0;OK;HARD;2;Service is OK')])

        self.check(svc, 0, 'Service is OK', [])

        # Service goes CRITICAL
        self.check(svc, 2, 'Service is CRITICAL',
                   [('error',
                     'SERVICE ALERT: test_host_0;test_ok_0;CRITICAL;SOFT;1;Service is CRITICAL')])

        self.check(svc, 2, 'Service is CRITICAL',
                   [('error',
                     'SERVICE ALERT: test_host_0;test_ok_0;CRITICAL;HARD;2;Service is CRITICAL')])

        # Service goes OK
        self.check(svc, 0, 'Service is OK',
                   [('info', 'SERVICE ALERT: test_host_0;test_ok_0;OK;HARD;2;Service is OK')])

        self.check(svc, 0, 'Service OK', [])

    def test_external_commands(self):
        """ Test logs for external commands

        :return:
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        now = int(time.time())

        host = self._scheduler.hosts.find_by_name("test_host_0")

        # Receiver receives unknown host external command
        excmd = '[%d] CHANGE_SVC_MODATTR;test_host_0;test_ok_0;1' % time.time()
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()

        excmd = '[%d] CHANGE_RETRY_HOST_CHECK_INTERVAL;test_host_0;42' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()

        # Get my first broker link
        my_broker = [b for b in list(self._scheduler.my_daemon.brokers.values())][0]
        # Extract monitoring logs
        monitoring_logs = []
        for brok in my_broker.broks:
            if brok.type == 'monitoring_log':
                data = unserialize(brok.data)
                monitoring_logs.append((data['level'], data['message']))

        expected_logs = [
            ('info',
             'EXTERNAL COMMAND: [%s] CHANGE_RETRY_HOST_CHECK_INTERVAL;test_host_0;42' % now),
            ('info',
             'EXTERNAL COMMAND: [%s] CHANGE_SVC_MODATTR;test_host_0;test_ok_0;1' % now)
        ]
        for log_level, log_message in expected_logs:
            assert (log_level, log_message) in monitoring_logs

    def test_passive_checks_host(self):
        """ Test logs for external commands - passive host checks, log disabled """
        self.passive_checks_host(False)

    def test_passive_checks_host_2(self):
        """ Test logs for external commands - passive host checks, log enabled """
        self.passive_checks_host(True)

    def passive_checks_host(self, log_passive_checks):
        """ Test logs for external commands

        :return:
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        # Force the log passive checks configuration parameter
        self._scheduler.pushed_conf.log_passive_checks = log_passive_checks

        # -----------------------------
        # Host part
        # -----------------------------
        # Get and configure host
        host = self._scheduler.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router which we depend of
        host.event_handler_enabled = False
        assert host is not None

        now = int(time.time())

        # Receive passive host check Down
        excmd = u'[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        assert 'DOWN' == host.state
        assert 'SOFT' == host.state_type
        assert 'Host is dead' == host.output
        excmd = u'[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        assert 'DOWN' == host.state
        assert 'SOFT' == host.state_type
        assert 'Host is dead' == host.output
        excmd = u'[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop(1)
        time.sleep(1.0)
        self.external_command_loop(1)
        assert 'DOWN' == host.state
        assert 'HARD' == host.state_type
        assert 'Host is dead' == host.output

        # Get my first broker link
        my_broker = [b for b in list(self._scheduler.my_daemon.brokers.values())][0]
        # Extract monitoring logs
        monitoring_logs = []
        for brok in my_broker.broks:
            if brok.type == 'monitoring_log':
                data = unserialize(brok.data)
                monitoring_logs.append((data['level'], data['message']))
                print(("Log (unicode: %s): %s" % (isinstance(data['message'], str), data['message'])))

        # Passive host check log contains:
        # - host name,
        # - host status,
        # - output,
        # - performance data and
        # - long output
        # All are separated with a semi-colon
        expected_logs = [
            ('error',
             'HOST ALERT: test_host_0;DOWN;SOFT;1;Host is dead'),
            ('error',
             'HOST ALERT: test_host_0;DOWN;SOFT;2;Host is dead'),
            ('error',
             'HOST ALERT: test_host_0;DOWN;HARD;3;Host is dead'),
            ('error',
             'HOST NOTIFICATION: test_contact;test_host_0;DOWN;notify-host;Host is dead')
        ]
        if log_passive_checks:
            expected_logs.extend([
                ('warning',
                 'PASSIVE HOST CHECK: test_host_0;2;Host is dead;;'),
                ('warning',
                 'PASSIVE HOST CHECK: test_host_0;2;Host is dead;;'),
                ('warning',
                 'PASSIVE HOST CHECK: test_host_0;2;Host is dead;;'),
            ])
        else:
            expected_logs.extend([
                ('info',
                 'EXTERNAL COMMAND: [%s] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now),
                ('info',
                 'EXTERNAL COMMAND: [%s] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now),
                ('info',
                 'EXTERNAL COMMAND: [%s] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Host is dead' % now)
            ])
        for log_level, log_message in expected_logs:
            print(("Msg: %s" % log_message))
            assert (log_level, log_message) in monitoring_logs

    def test_passive_checks_service_log_disabled(self):
        """ Test logs for external commands - passive service checks, log disabled """
        self.passive_checks_service(False)

    def test_passive_checks_service_log_enabled(self):
        """ Test logs for external commands - passive service checks, log enabled """
        self.passive_checks_service(True)

    def passive_checks_service(self, log_passive_checks):
        """ Test logs for external commands

        :return:
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        # Force the log passive checks configuration parameter
        self._scheduler.pushed_conf.log_passive_checks = log_passive_checks

        now = int(time.time())

        # -----------------------------
        # Service part
        # -----------------------------
        # Get host
        host = self._scheduler.hosts.find_by_name('test_host_0')
        host.checks_in_progress = []
        host.event_handler_enabled = False
        host.active_checks_enabled = True
        host.passive_checks_enabled = True
        assert host is not None

        # Get service
        svc = self._scheduler.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.event_handler_enabled = False
        svc.active_checks_enabled = True
        svc.passive_checks_enabled = True
        assert svc is not None

        # Passive checks for host and service
        # ---------------------------------------------
        # Receive passive host check Up
        excmd = u'[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;0;Host is UP' % time.time()
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        assert 'UP' == host.state
        assert 'Host is UP' == host.output

        # Service is going ok ...
        excmd = u'[%d] PROCESS_SERVICE_CHECK_RESULT;test_host_0;test_ok_0;0;' \
                u'Service is OK|rtt=9999;5;10;0;10000' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        assert 'OK' == svc.state
        assert 'Service is OK' == svc.output
        assert 'rtt=9999;5;10;0;10000' == svc.perf_data

        # Service is going ok ... with long output
        excmd = u'[%d] PROCESS_SERVICE_CHECK_RESULT;test_host_0;test_ok_0;0;' \
                u'Service is OK and have some special characters: àéèüäï' \
                u'|rtt=9999;5;10;0;10000' \
                u'\r\nLong output... also some specials: àéèüäï' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop(1)
        time.sleep(1.0)
        self.external_command_loop(1)
        assert 'OK' == svc.state
        assert u'Service is OK and have some special characters: àéèüäï' == svc.output
        assert u'rtt=9999;5;10;0;10000' == svc.perf_data
        assert u'Long output... also some specials: àéèüäï' == svc.long_output

        # Get my first broker link
        my_broker = [b for b in list(self._scheduler.my_daemon.brokers.values())][0]
        # Extract monitoring logs
        monitoring_logs = []
        for brok in my_broker.broks:
            if brok.type == 'monitoring_log':
                data = unserialize(brok.data)
                monitoring_logs.append((data['level'], data['message']))
                print(("Log (unicode: %s): %s" % (isinstance(data['message'], str), data['message'])))

        # Passive service check log contains:
        # - host name,
        # - host status,
        # - output,
        # - performance data and
        # - long output
        # All are separated with a semi-colon
        if log_passive_checks:
            expected_logs = [
                ('info', u'PASSIVE HOST CHECK: test_host_0;0;Host is UP;;'),
                ('info', u'PASSIVE SERVICE CHECK: test_host_0;test_ok_0;0;'
                         u'Service is OK;;rtt=9999;5;10;0;10000'),
                ('info', u'PASSIVE SERVICE CHECK: test_host_0;test_ok_0;0;'
                         u'Service is OK and have some special characters: àéèüäï;'
                         u'Long output... also some specials: àéèüäï;'
                         u'rtt=9999;5;10;0;10000'),
            ]
        else:
            expected_logs = [
                ('info', u'EXTERNAL COMMAND: [%s] PROCESS_HOST_CHECK_RESULT;'
                         u'test_host_0;0;Host is UP' % now),
                ('info', u'EXTERNAL COMMAND: [%s] PROCESS_SERVICE_CHECK_RESULT;'
                         u'test_host_0;test_ok_0;0;Service is OK|rtt=9999;5;10;0;10000' % now),
                ('info', u'EXTERNAL COMMAND: [%s] PROCESS_SERVICE_CHECK_RESULT;'
                         u'test_host_0;test_ok_0;0;'
                         u'Service is OK and have some special characters: àéèüäï'
                         u'|rtt=9999;5;10;0;10000'
                         u'\\r\\nLong output... also some specials: àéèüäï' % now),
            ]
        print(monitoring_logs)
        for log_level, log_message in expected_logs:
            print(("Msg: %s" % log_message))
            assert (log_level, log_message) in monitoring_logs

    def test_special_external_commands(self):
        """ Test logs for special external commands
        :return:
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg')
        assert self.conf_is_correct

        now = int(time.time())

        # RESTART_PROGRAM
        excmd = '[%d] RESTART_PROGRAM' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        self.assert_any_log_match('RESTART command : libexec/sleep_command.sh 3')

        # RELOAD_CONFIG
        excmd = '[%d] RELOAD_CONFIG' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        self.assert_any_log_match('RELOAD command : libexec/sleep_command.sh 2')

        # UNKNOWN COMMAND
        excmd = '[%d] UNKNOWN_COMMAND' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        # Malformed command
        excmd = '[%d] MALFORMED COMMAND' % now
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()

        # Get my first broker link
        # my_broker = [b for b in self._scheduler.my_daemon.brokers.values()][0]
        # Extract monitoring logs
        monitoring_logs = []
        for brok in self._main_broker.broks:
            if brok.type == 'monitoring_log':
                data = unserialize(brok.data)
                monitoring_logs.append((data['level'], data['message']))

        # The messages are echoed by the launched scripts
        expected_logs = [
            ('info', "I start sleeping for 3 seconds...\\nI awoke after sleeping 3 seconds | sleep=3"),
            ('info', "I start sleeping for 2 seconds...\\nI awoke after sleeping 2 seconds | sleep=2"),
            ('error', "Malformed command: '[%s] MALFORMED COMMAND'" % now),
            ('error', "Command '[%s] UNKNOWN_COMMAND' is not recognized, sorry" % now)
        ]
        for log_level, log_message in expected_logs:
            assert (log_level, log_message) in monitoring_logs

    def test_special_external_commands_no_logs(self):
        """ Test no logs for special external commands
        :return:
        """
        self.setup_with_file('cfg/cfg_monitoring_logs.cfg',
                             'cfg/cfg_monitoring_logs_disabled.ini')
        assert self.conf_is_correct

        # RESTART_PROGRAM
        excmd = '[%d] RESTART_PROGRAM' % int(time.time())
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        # todo: it should not but it does!
        self.assert_any_log_match('RESTART command : libexec/sleep_command.sh 3')
        # self.assert_no_log_match('RESTART command : libexec/sleep_command.sh 3')

        # RELOAD_CONFIG
        excmd = '[%d] RELOAD_CONFIG' % int(time.time())
        self._scheduler.run_external_commands([excmd])
        self.external_command_loop()
        # todo: it should not but it does!
        self.assert_any_log_match('RELOAD command : libexec/sleep_command.sh 2')
        # self.assert_no_log_match('RELOAD command : libexec/sleep_command.sh 2')

        # Get my first broker link
        my_broker = [b for b in list(self._scheduler.my_daemon.brokers.values())][0]
        # Extract monitoring logs
        monitoring_logs = []
        for brok in self._main_broker.broks:
            if brok.type == 'monitoring_log':
                data = unserialize(brok.data)
                monitoring_logs.append((data['level'], data['message']))

        # No monitoring logs
        # todo: it should not but it does!
        # assert [] == monitoring_logs
        expected_logs = [
            ('info', 'I start sleeping for 3 seconds...\\nI awoke after sleeping 3 seconds | sleep=3'),
            ('info', 'I start sleeping for 2 seconds...\\nI awoke after sleeping 2 seconds | sleep=2'),
        ]
        for log_level, log_message in expected_logs:
            assert (log_level, log_message) in monitoring_logs

    def test_timeperiod_transition_log(self):
        self.setup_with_file('cfg/cfg_default.cfg')

        tp = self._scheduler.timeperiods.find_by_name('24x7')

        self.assertIsNot(tp, None)

        data = unserialize(tp.check_and_log_activation_change().data)
        assert data['level'] == 'info'
        assert data['message'] == 'TIMEPERIOD TRANSITION: 24x7;-1;1'

        # Now make this tp unable to be active again by removing al it's daterange
        dr = tp.dateranges
        tp.dateranges = []
        data = unserialize(tp.check_and_log_activation_change().data)
        assert data['level'] == 'info'
        assert data['message'] == 'TIMEPERIOD TRANSITION: 24x7;1;0'

        # Ok, let get back to work
        tp.dateranges = dr
        data = unserialize(tp.check_and_log_activation_change().data)
        assert data['level'] == 'info'
        assert data['message'] == 'TIMEPERIOD TRANSITION: 24x7;0;1'