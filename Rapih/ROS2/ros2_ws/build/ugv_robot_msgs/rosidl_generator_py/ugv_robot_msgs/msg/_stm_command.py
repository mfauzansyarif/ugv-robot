# generated from rosidl_generator_py/resource/_idl.py.em
# with input from ugv_robot_msgs:msg/StmCommand.idl
# generated code does not contain a copyright notice


# Import statements for member types

# Member 'act'
import numpy  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_StmCommand(type):
    """Metaclass of message 'StmCommand'."""

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
                'ugv_robot_msgs.msg.StmCommand')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__stm_command
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__stm_command
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__stm_command
            cls._TYPE_SUPPORT = module.type_support_msg__msg__stm_command
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__stm_command

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class StmCommand(metaclass=Metaclass_StmCommand):
    """Message class 'StmCommand'."""

    __slots__ = [
        '_speed',
        '_act',
        '_f_lamp',
        '_b_lamp',
        '_b_lamp_mode',
        '_pantilt_horizontal',
        '_pantilt_vertical',
        '_kamera_zoom',
        '_slip_ring',
        '_lrf_trigger',
        '_gcs_reply_stm32_status',
        '_gcs_reply_lrf_status',
        '_gcs_reply_lrf_lsb',
        '_gcs_reply_lrf_msb',
        '_gcs_reply_box_terdeteksi',
        '_gcs_reply_box_pusat_x',
        '_gcs_reply_box_pusat_y',
        '_gcs_reply_box_lebar',
        '_gcs_reply_box_tinggi',
    ]

    _fields_and_field_types = {
        'speed': 'int8',
        'act': 'int8[8]',
        'f_lamp': 'uint8',
        'b_lamp': 'uint8',
        'b_lamp_mode': 'uint8',
        'pantilt_horizontal': 'int8',
        'pantilt_vertical': 'int8',
        'kamera_zoom': 'int8',
        'slip_ring': 'uint8',
        'lrf_trigger': 'uint8',
        'gcs_reply_stm32_status': 'uint8',
        'gcs_reply_lrf_status': 'uint8',
        'gcs_reply_lrf_lsb': 'uint8',
        'gcs_reply_lrf_msb': 'uint8',
        'gcs_reply_box_terdeteksi': 'uint8',
        'gcs_reply_box_pusat_x': 'int8',
        'gcs_reply_box_pusat_y': 'int8',
        'gcs_reply_box_lebar': 'uint8',
        'gcs_reply_box_tinggi': 'uint8',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.Array(rosidl_parser.definition.BasicType('int8'), 8),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.speed = kwargs.get('speed', int())
        if 'act' not in kwargs:
            self.act = numpy.zeros(8, dtype=numpy.int8)
        else:
            self.act = numpy.array(kwargs.get('act'), dtype=numpy.int8)
            assert self.act.shape == (8, )
        self.f_lamp = kwargs.get('f_lamp', int())
        self.b_lamp = kwargs.get('b_lamp', int())
        self.b_lamp_mode = kwargs.get('b_lamp_mode', int())
        self.pantilt_horizontal = kwargs.get('pantilt_horizontal', int())
        self.pantilt_vertical = kwargs.get('pantilt_vertical', int())
        self.kamera_zoom = kwargs.get('kamera_zoom', int())
        self.slip_ring = kwargs.get('slip_ring', int())
        self.lrf_trigger = kwargs.get('lrf_trigger', int())
        self.gcs_reply_stm32_status = kwargs.get('gcs_reply_stm32_status', int())
        self.gcs_reply_lrf_status = kwargs.get('gcs_reply_lrf_status', int())
        self.gcs_reply_lrf_lsb = kwargs.get('gcs_reply_lrf_lsb', int())
        self.gcs_reply_lrf_msb = kwargs.get('gcs_reply_lrf_msb', int())
        self.gcs_reply_box_terdeteksi = kwargs.get('gcs_reply_box_terdeteksi', int())
        self.gcs_reply_box_pusat_x = kwargs.get('gcs_reply_box_pusat_x', int())
        self.gcs_reply_box_pusat_y = kwargs.get('gcs_reply_box_pusat_y', int())
        self.gcs_reply_box_lebar = kwargs.get('gcs_reply_box_lebar', int())
        self.gcs_reply_box_tinggi = kwargs.get('gcs_reply_box_tinggi', int())

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
        if self.speed != other.speed:
            return False
        if all(self.act != other.act):
            return False
        if self.f_lamp != other.f_lamp:
            return False
        if self.b_lamp != other.b_lamp:
            return False
        if self.b_lamp_mode != other.b_lamp_mode:
            return False
        if self.pantilt_horizontal != other.pantilt_horizontal:
            return False
        if self.pantilt_vertical != other.pantilt_vertical:
            return False
        if self.kamera_zoom != other.kamera_zoom:
            return False
        if self.slip_ring != other.slip_ring:
            return False
        if self.lrf_trigger != other.lrf_trigger:
            return False
        if self.gcs_reply_stm32_status != other.gcs_reply_stm32_status:
            return False
        if self.gcs_reply_lrf_status != other.gcs_reply_lrf_status:
            return False
        if self.gcs_reply_lrf_lsb != other.gcs_reply_lrf_lsb:
            return False
        if self.gcs_reply_lrf_msb != other.gcs_reply_lrf_msb:
            return False
        if self.gcs_reply_box_terdeteksi != other.gcs_reply_box_terdeteksi:
            return False
        if self.gcs_reply_box_pusat_x != other.gcs_reply_box_pusat_x:
            return False
        if self.gcs_reply_box_pusat_y != other.gcs_reply_box_pusat_y:
            return False
        if self.gcs_reply_box_lebar != other.gcs_reply_box_lebar:
            return False
        if self.gcs_reply_box_tinggi != other.gcs_reply_box_tinggi:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def speed(self):
        """Message field 'speed'."""
        return self._speed

    @speed.setter
    def speed(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'speed' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'speed' field must be an integer in [-128, 127]"
        self._speed = value

    @property
    def act(self):
        """Message field 'act'."""
        return self._act

    @act.setter
    def act(self, value):
        if isinstance(value, numpy.ndarray):
            assert value.dtype == numpy.int8, \
                "The 'act' numpy.ndarray() must have the dtype of 'numpy.int8'"
            assert value.size == 8, \
                "The 'act' numpy.ndarray() must have a size of 8"
            self._act = value
            return
        if __debug__:
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 len(value) == 8 and
                 all(isinstance(v, int) for v in value) and
                 all(val >= -128 and val < 128 for val in value)), \
                "The 'act' field must be a set or sequence with length 8 and each value of type 'int' and each integer in [-128, 127]"
        self._act = numpy.array(value, dtype=numpy.int8)

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
    def b_lamp_mode(self):
        """Message field 'b_lamp_mode'."""
        return self._b_lamp_mode

    @b_lamp_mode.setter
    def b_lamp_mode(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'b_lamp_mode' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'b_lamp_mode' field must be an unsigned integer in [0, 255]"
        self._b_lamp_mode = value

    @property
    def pantilt_horizontal(self):
        """Message field 'pantilt_horizontal'."""
        return self._pantilt_horizontal

    @pantilt_horizontal.setter
    def pantilt_horizontal(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'pantilt_horizontal' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'pantilt_horizontal' field must be an integer in [-128, 127]"
        self._pantilt_horizontal = value

    @property
    def pantilt_vertical(self):
        """Message field 'pantilt_vertical'."""
        return self._pantilt_vertical

    @pantilt_vertical.setter
    def pantilt_vertical(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'pantilt_vertical' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'pantilt_vertical' field must be an integer in [-128, 127]"
        self._pantilt_vertical = value

    @property
    def kamera_zoom(self):
        """Message field 'kamera_zoom'."""
        return self._kamera_zoom

    @kamera_zoom.setter
    def kamera_zoom(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'kamera_zoom' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'kamera_zoom' field must be an integer in [-128, 127]"
        self._kamera_zoom = value

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
    def lrf_trigger(self):
        """Message field 'lrf_trigger'."""
        return self._lrf_trigger

    @lrf_trigger.setter
    def lrf_trigger(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'lrf_trigger' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'lrf_trigger' field must be an unsigned integer in [0, 255]"
        self._lrf_trigger = value

    @property
    def gcs_reply_stm32_status(self):
        """Message field 'gcs_reply_stm32_status'."""
        return self._gcs_reply_stm32_status

    @gcs_reply_stm32_status.setter
    def gcs_reply_stm32_status(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_stm32_status' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_stm32_status' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_stm32_status = value

    @property
    def gcs_reply_lrf_status(self):
        """Message field 'gcs_reply_lrf_status'."""
        return self._gcs_reply_lrf_status

    @gcs_reply_lrf_status.setter
    def gcs_reply_lrf_status(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_lrf_status' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_lrf_status' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_lrf_status = value

    @property
    def gcs_reply_lrf_lsb(self):
        """Message field 'gcs_reply_lrf_lsb'."""
        return self._gcs_reply_lrf_lsb

    @gcs_reply_lrf_lsb.setter
    def gcs_reply_lrf_lsb(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_lrf_lsb' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_lrf_lsb' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_lrf_lsb = value

    @property
    def gcs_reply_lrf_msb(self):
        """Message field 'gcs_reply_lrf_msb'."""
        return self._gcs_reply_lrf_msb

    @gcs_reply_lrf_msb.setter
    def gcs_reply_lrf_msb(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_lrf_msb' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_lrf_msb' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_lrf_msb = value

    @property
    def gcs_reply_box_terdeteksi(self):
        """Message field 'gcs_reply_box_terdeteksi'."""
        return self._gcs_reply_box_terdeteksi

    @gcs_reply_box_terdeteksi.setter
    def gcs_reply_box_terdeteksi(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_box_terdeteksi' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_box_terdeteksi' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_box_terdeteksi = value

    @property
    def gcs_reply_box_pusat_x(self):
        """Message field 'gcs_reply_box_pusat_x'."""
        return self._gcs_reply_box_pusat_x

    @gcs_reply_box_pusat_x.setter
    def gcs_reply_box_pusat_x(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_box_pusat_x' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'gcs_reply_box_pusat_x' field must be an integer in [-128, 127]"
        self._gcs_reply_box_pusat_x = value

    @property
    def gcs_reply_box_pusat_y(self):
        """Message field 'gcs_reply_box_pusat_y'."""
        return self._gcs_reply_box_pusat_y

    @gcs_reply_box_pusat_y.setter
    def gcs_reply_box_pusat_y(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_box_pusat_y' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'gcs_reply_box_pusat_y' field must be an integer in [-128, 127]"
        self._gcs_reply_box_pusat_y = value

    @property
    def gcs_reply_box_lebar(self):
        """Message field 'gcs_reply_box_lebar'."""
        return self._gcs_reply_box_lebar

    @gcs_reply_box_lebar.setter
    def gcs_reply_box_lebar(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_box_lebar' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_box_lebar' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_box_lebar = value

    @property
    def gcs_reply_box_tinggi(self):
        """Message field 'gcs_reply_box_tinggi'."""
        return self._gcs_reply_box_tinggi

    @gcs_reply_box_tinggi.setter
    def gcs_reply_box_tinggi(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'gcs_reply_box_tinggi' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'gcs_reply_box_tinggi' field must be an unsigned integer in [0, 255]"
        self._gcs_reply_box_tinggi = value
