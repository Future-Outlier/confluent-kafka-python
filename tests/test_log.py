#!/usr/bin/env python

from io import StringIO
import logging

import confluent_kafka
import confluent_kafka.avro
import confluent_kafka.admin

from tests.common import TestConsumer
from tests.common.schema_registry import TestAvroConsumer


class CountingFilter(logging.Filter):
    def __init__(self, name):
        self.name = name
        self.cnt = 0

    def filter(self, record):
        print(self.name, record.getMessage())
        self.cnt += 1
        print(record)


def _setup_string_buffer_logger(name):
    stringBuffer = StringIO()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stringBuffer)
    handler.setFormatter(logging.Formatter('%(name)s Logger | %(message)s'))
    logger.addHandler(handler)
    return stringBuffer, logger


def test_logging_consumer():
    """ Tests that logging works """

    logger = logging.getLogger('consumer')
    logger.setLevel(logging.DEBUG)
    f = CountingFilter('consumer')
    logger.addFilter(f)
    kc = TestConsumer({'group.id': 'test',
                       'debug': 'all'},
                      logger=logger)
    while f.cnt == 0:
        kc.poll(timeout=0.5)

    print('%s: %d log messages seen' % (f.name, f.cnt))

    kc.close()


def test_logging_avro_consumer():
    """ Tests that logging works """

    logger = logging.getLogger('avroconsumer')
    logger.setLevel(logging.DEBUG)
    f = CountingFilter('avroconsumer')
    logger.addFilter(f)

    kc = TestAvroConsumer({'schema.registry.url': 'http://example.com',
                           'group.id': 'test',
                           'debug': 'all'},
                          logger=logger)
    while f.cnt == 0:
        kc.poll(timeout=0.5)

    print('%s: %d log messages seen' % (f.name, f.cnt))

    kc.close()


def test_logging_producer():
    """ Tests that logging works """

    logger = logging.getLogger('producer')
    logger.setLevel(logging.DEBUG)
    f = CountingFilter('producer')
    logger.addFilter(f)

    p = confluent_kafka.Producer({'debug': 'all'}, logger=logger)

    while f.cnt == 0:
        p.poll(timeout=0.5)

    print('%s: %d log messages seen' % (f.name, f.cnt))


def test_logging_avro_producer():
    """ Tests that logging works """

    logger = logging.getLogger('avroproducer')
    logger.setLevel(logging.DEBUG)
    f = CountingFilter('avroproducer')
    logger.addFilter(f)

    p = confluent_kafka.avro.AvroProducer({'schema.registry.url': 'http://example.com',
                                           'debug': 'all'},
                                          logger=logger)

    while f.cnt == 0:
        p.poll(timeout=0.5)

    print('%s: %d log messages seen' % (f.name, f.cnt))


def test_logging_constructor():
    """ Verify different forms of constructors """

    for how in ['dict', 'dict+kwarg', 'kwarg']:
        logger = logging.getLogger('producer: ' + how)
        logger.setLevel(logging.DEBUG)
        f = CountingFilter(logger.name)
        logger.addFilter(f)

        if how == 'dict':
            p = confluent_kafka.Producer({'debug': 'all', 'logger': logger})
        elif how == 'dict+kwarg':
            p = confluent_kafka.Producer({'debug': 'all'}, logger=logger)
        elif how == 'kwarg':
            conf = {'debug': 'all', 'logger': logger}
            p = confluent_kafka.Producer(**conf)
        else:
            raise RuntimeError('Not reached')

        print('Test %s with %s' % (p, how))

        while f.cnt == 0:
            p.poll(timeout=0.5)

        print('%s: %s: %d log messages seen' % (how, f.name, f.cnt))


def test_producer_logger_logging_in_given_format():
    """Test that asserts that logging is working by matching part of the log message"""

    stringBuffer, logger = _setup_string_buffer_logger('Producer')

    p = confluent_kafka.Producer(
        {"bootstrap.servers": "test", "logger": logger, "debug": "msg"})
    val = 1
    while val > 0:
        val = p.flush()
    logMessage = stringBuffer.getvalue().strip()
    stringBuffer.close()
    print(logMessage)

    assert "Producer Logger | INIT" in logMessage


def test_consumer_logger_logging_in_given_format():
    """Test that asserts that logging is working by matching part of the log message"""

    stringBuffer, logger = _setup_string_buffer_logger('Consumer')

    c = TestConsumer(
        {"bootstrap.servers": "test", "group.id": "test", "logger": logger, "debug": "msg"})
    c.poll(0)

    logMessage = stringBuffer.getvalue().strip()
    stringBuffer.close()
    c.close()

    assert "Consumer Logger | INIT" in logMessage


def test_admin_logger_logging_in_given_format_when_provided_in_conf():
    """Test that asserts that logging is working by matching part of the log message"""

    stringBuffer, logger = _setup_string_buffer_logger('Admin')

    admin_client = confluent_kafka.admin.AdminClient(
        {"bootstrap.servers": "test", "logger": logger, "debug": "admin"})
    admin_client.poll(0)

    logMessage = stringBuffer.getvalue().strip()
    stringBuffer.close()

    assert "Admin Logger | INIT" in logMessage


def test_admin_logger_logging_in_given_format_when_provided_as_admin_client_argument():
    """Test that asserts that logging is working by matching part of the log message"""

    stringBuffer, logger = _setup_string_buffer_logger('Admin')

    admin_client = confluent_kafka.admin.AdminClient(
        {"bootstrap.servers": "test", "debug": "admin"}, logger=logger)
    admin_client.poll(0)

    logMessage = stringBuffer.getvalue().strip()
    stringBuffer.close()

    assert "Admin Logger | INIT" in logMessage
