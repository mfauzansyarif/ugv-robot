# generated from rosidl_generator_py/resource/_idl.py.em
# with input from ugv_robot_msgs:msg/PersonDetection.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_PersonDetection(type):
    """Metaclass of message 'PersonDetection'."""

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
                'ugv_robot_msgs.msg.PersonDetection')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__person_detection
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__person_detection
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__person_detection
            cls._TYPE_SUPPORT = module.type_support_msg__msg__person_detection
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__person_detection

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class PersonDetection(metaclass=Metaclass_PersonDetection):
    """Message class 'PersonDetection'."""

    __slots__ = [
        '_terdeteksi',
        '_pusat_x',
        '_pusat_y',
        '_lebar',
        '_tinggi',
        '_confidence',
    ]

    _fields_and_field_types = {
        'terdeteksi': 'boolean',
        'pusat_x': 'float',
        'pusat_y': 'float',
        'lebar': 'float',
        'tinggi': 'float',
        'confidence': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.terdeteksi = kwargs.get('terdeteksi', bool())
        self.pusat_x = kwargs.get('pusat_x', float())
        self.pusat_y = kwargs.get('pusat_y', float())
        self.lebar = kwargs.get('lebar', float())
        self.tinggi = kwargs.get('tinggi', float())
        self.confidence = kwargs.get('confidence', float())

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
        if self.terdeteksi != other.terdeteksi:
            return False
        if self.pusat_x != other.pusat_x:
            return False
        if self.pusat_y != other.pusat_y:
            return False
        if self.lebar != other.lebar:
            return False
        if self.tinggi != other.tinggi:
            return False
        if self.confidence != other.confidence:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def terdeteksi(self):
        """Message field 'terdeteksi'."""
        return self._terdeteksi

    @terdeteksi.setter
    def terdeteksi(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'terdeteksi' field must be of type 'bool'"
        self._terdeteksi = value

    @property
    def pusat_x(self):
        """Message field 'pusat_x'."""
        return self._pusat_x

    @pusat_x.setter
    def pusat_x(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'pusat_x' field must be of type 'float'"
        self._pusat_x = value

    @property
    def pusat_y(self):
        """Message field 'pusat_y'."""
        return self._pusat_y

    @pusat_y.setter
    def pusat_y(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'pusat_y' field must be of type 'float'"
        self._pusat_y = value

    @property
    def lebar(self):
        """Message field 'lebar'."""
        return self._lebar

    @lebar.setter
    def lebar(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'lebar' field must be of type 'float'"
        self._lebar = value

    @property
    def tinggi(self):
        """Message field 'tinggi'."""
        return self._tinggi

    @tinggi.setter
    def tinggi(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'tinggi' field must be of type 'float'"
        self._tinggi = value

    @property
    def confidence(self):
        """Message field 'confidence'."""
        return self._confidence

    @confidence.setter
    def confidence(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'confidence' field must be of type 'float'"
        self._confidence = value
