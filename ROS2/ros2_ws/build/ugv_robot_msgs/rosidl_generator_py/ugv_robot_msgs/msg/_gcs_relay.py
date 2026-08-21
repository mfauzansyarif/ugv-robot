# generated from rosidl_generator_py/resource/_idl.py.em
# with input from ugv_robot_msgs:msg/GcsRelay.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_GcsRelay(type):
    """Metaclass of message 'GcsRelay'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('ugv_robot_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'ugv_robot_msgs.msg.GcsRelay')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__gcs_relay
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__gcs_relay
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__gcs_relay
            cls._TYPE_SUPPORT = module.type_support_msg__msg__gcs_relay
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__gcs_relay

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GcsRelay(metaclass=Metaclass_GcsRelay):
    """Message class 'GcsRelay'."""

    __slots__ = [
        '_estop',
        '_x_joy1',
        '_y_joy1',
        '_x_joy2',
        '_y_joy2',
        '_zoom',
        '_lrf',
        '_f_lamp',
        '_b_lamp',
        '_slip_ring',
        '_body_up_down',
        '_motor_individual_id',
        '_motor_individual_arah',
        '_kalibrasi',
        '_mode',
    ]

    _fields_and_field_types = {
        'estop': 'uint8',
        'x_joy1': 'int8',
        'y_joy1': 'int8',
        'x_joy2': 'int8',
        'y_joy2': 'int8',
        'zoom': 'int8',
        'lrf': 'uint8',
        'f_lamp': 'uint8',
        'b_lamp': 'uint8',
        'slip_ring': 'uint8',
        'body_up_down': 'int8',
        'motor_individual_id': 'uint8',
        'motor_individual_arah': 'int8',
        'kalibrasi': 'uint8',
        'mode': 'uint8',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.estop = kwargs.get('estop', int())
        self.x_joy1 = kwargs.get('x_joy1', int())
        self.y_joy1 = kwargs.get('y_joy1', int())
        self.x_joy2 = kwargs.get('x_joy2', int())
        self.y_joy2 = kwargs.get('y_joy2', int())
        self.zoom = kwargs.get('zoom', int())
        self.lrf = kwargs.get('lrf', int())
        self.f_lamp = kwargs.get('f_lamp', int())
        self.b_lamp = kwargs.get('b_lamp', int())
        self.slip_ring = kwargs.get('slip_ring', int())
        self.body_up_down = kwargs.get('body_up_down', int())
        self.motor_individual_id = kwargs.get('motor_individual_id', int())
        self.motor_individual_arah = kwargs.get('motor_individual_arah', int())
        self.kalibrasi = kwargs.get('kalibrasi', int())
        self.mode = kwargs.get('mode', int())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.estop != other.estop:
            return False
        if self.x_joy1 != other.x_joy1:
            return False
        if self.y_joy1 != other.y_joy1:
            return False
        if self.x_joy2 != other.x_joy2:
            return False
        if self.y_joy2 != other.y_joy2:
            return False
        if self.zoom != other.zoom:
            return False
        if self.lrf != other.lrf:
            return False
        if self.f_lamp != other.f_lamp:
            return False
        if self.b_lamp != other.b_lamp:
            return False
        if self.slip_ring != other.slip_ring:
            return False
        if self.body_up_down != other.body_up_down:
            return False
        if self.motor_individual_id != other.motor_individual_id:
            return False
        if self.motor_individual_arah != other.motor_individual_arah:
            return False
        if self.kalibrasi != other.kalibrasi:
            return False
        if self.mode != other.mode:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def estop(self):
        """Message field 'estop'."""
        return self._estop

    @estop.setter
    def estop(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'estop' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'estop' field must be an unsigned integer in [0, 255]"
        self._estop = value

    @property
    def x_joy1(self):
        """Message field 'x_joy1'."""
        return self._x_joy1

    @x_joy1.setter
    def x_joy1(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'x_joy1' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'x_joy1' field must be an integer in [-128, 127]"
        self._x_joy1 = value

    @property
    def y_joy1(self):
        """Message field 'y_joy1'."""
        return self._y_joy1

    @y_joy1.setter
    def y_joy1(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'y_joy1' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'y_joy1' field must be an integer in [-128, 127]"
        self._y_joy1 = value

    @property
    def x_joy2(self):
        """Message field 'x_joy2'."""
        return self._x_joy2

    @x_joy2.setter
    def x_joy2(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'x_joy2' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'x_joy2' field must be an integer in [-128, 127]"
        self._x_joy2 = value

    @property
    def y_joy2(self):
        """Message field 'y_joy2'."""
        return self._y_joy2

    @y_joy2.setter
    def y_joy2(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'y_joy2' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'y_joy2' field must be an integer in [-128, 127]"
        self._y_joy2 = value

    @property
    def zoom(self):
        """Message field 'zoom'."""
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'zoom' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'zoom' field must be an integer in [-128, 127]"
        self._zoom = value

    @property
    def lrf(self):
        """Message field 'lrf'."""
        return self._lrf

    @lrf.setter
    def lrf(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'lrf' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'lrf' field must be an unsigned integer in [0, 255]"
        self._lrf = value

    @property
    def f_lamp(self):
        """Message field 'f_lamp'."""
        return self._f_lamp

    @f_lamp.setter
    def f_lamp(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'f_lamp' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'f_lamp' field must be an unsigned integer in [0, 255]"
        self._f_lamp = value

    @property
    def b_lamp(self):
        """Message field 'b_lamp'."""
        return self._b_lamp

    @b_lamp.setter
    def b_lamp(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'b_lamp' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'b_lamp' field must be an unsigned integer in [0, 255]"
        self._b_lamp = value

    @property
    def slip_ring(self):
        """Message field 'slip_ring'."""
        return self._slip_ring

    @slip_ring.setter
    def slip_ring(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'slip_ring' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'slip_ring' field must be an unsigned integer in [0, 255]"
        self._slip_ring = value

    @property
    def body_up_down(self):
        """Message field 'body_up_down'."""
        return self._body_up_down

    @body_up_down.setter
    def body_up_down(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'body_up_down' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'body_up_down' field must be an integer in [-128, 127]"
        self._body_up_down = value

    @property
    def motor_individual_id(self):
        """Message field 'motor_individual_id'."""
        return self._motor_individual_id

    @motor_individual_id.setter
    def motor_individual_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'motor_individual_id' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'motor_individual_id' field must be an unsigned integer in [0, 255]"
        self._motor_individual_id = value

    @property
    def motor_individual_arah(self):
        """Message field 'motor_individual_arah'."""
        return self._motor_individual_arah

    @motor_individual_arah.setter
    def motor_individual_arah(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'motor_individual_arah' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'motor_individual_arah' field must be an integer in [-128, 127]"
        self._motor_individual_arah = value

    @property
    def kalibrasi(self):
        """Message field 'kalibrasi'."""
        return self._kalibrasi

    @kalibrasi.setter
    def kalibrasi(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'kalibrasi' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'kalibrasi' field must be an unsigned integer in [0, 255]"
        self._kalibrasi = value

    @property
    def mode(self):
        """Message field 'mode'."""
        return self._mode

    @mode.setter
    def mode(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'mode' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'mode' field must be an unsigned integer in [0, 255]"
        self._mode = value
