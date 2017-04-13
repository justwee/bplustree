import abc

from .const import (ENDIAN, KEY_BYTES, VALUE_BYTES, PAGE_REFERENCE_BYTES,
                    USED_KEY_LENGTH_BYTES, USED_VALUE_LENGTH_BYTES)


class Entry(abc.ABC):

    key = None

    @abc.abstractmethod
    def load(self, data: bytes):
        pass

    @abc.abstractmethod
    def dump(self) -> bytes:
        pass

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __le__(self, other):
        return self.key <= other.key

    def __gt__(self, other):
        return self.key > other.key

    def __ge__(self, other):
        return self.key >= other.key


class Record(Entry):
    """A container for the actual data the tree stores."""

    length = (USED_KEY_LENGTH_BYTES + KEY_BYTES +
              USED_VALUE_LENGTH_BYTES + VALUE_BYTES)

    def __init__(self, key=None, value: bytes=None, data: bytes=None):
        self.key = key
        self.value = value
        if data:
            self.load(data)

    def load(self, data: bytes):
        assert len(data) == self.length

        end_used_key_length = USED_KEY_LENGTH_BYTES
        used_key_length = int.from_bytes(data[0:end_used_key_length], ENDIAN)
        assert 0 <= used_key_length <= KEY_BYTES

        end_key = end_used_key_length + used_key_length
        self.key = int.from_bytes(data[end_used_key_length:end_key], ENDIAN)

        start_used_value_length = end_used_key_length + KEY_BYTES
        end_used_value_length = end_key + USED_VALUE_LENGTH_BYTES
        used_value_length = int.from_bytes(
            data[start_used_value_length:end_used_value_length], ENDIAN
        )
        assert 0 <= used_value_length <= VALUE_BYTES

        end_value = end_used_value_length + used_value_length
        self.value = data[end_used_value_length:end_value]

    def dump(self) -> bytes:
        assert isinstance(self.key, int)
        assert isinstance(self.value, bytes)
        key_as_bytes = self.key.to_bytes(KEY_BYTES, ENDIAN)
        used_key_length = len(key_as_bytes)
        used_value_length = len(self.value)
        data = (
            used_key_length.to_bytes(USED_VALUE_LENGTH_BYTES, ENDIAN) +
            key_as_bytes +
            bytes(KEY_BYTES - used_key_length) +
            used_value_length.to_bytes(USED_VALUE_LENGTH_BYTES, ENDIAN) +
            self.value +
            bytes(VALUE_BYTES - used_value_length)
        )
        return data

    def __repr__(self):
        return '<Record: {} value={}>'.format(
            self.key, self.value
        )


class Reference(Entry):
    """A container for a reference to other nodes."""

    length = 2 * PAGE_REFERENCE_BYTES + USED_KEY_LENGTH_BYTES + KEY_BYTES

    def __init__(self, key=None, before=None, after=None, data: bytes=None):
        self.key = key
        self.before = before
        self.after = after
        if data:
            self.load(data)

    def load(self, data: bytes):
        assert len(data) == self.length
        end_before = PAGE_REFERENCE_BYTES
        self.before = int.from_bytes(data[0:end_before], ENDIAN)

        end_used_key_length = end_before + USED_KEY_LENGTH_BYTES
        used_key_length = int.from_bytes(
            data[end_before:end_used_key_length], ENDIAN
        )
        assert 0 <= used_key_length <= KEY_BYTES

        end_key = end_used_key_length + used_key_length
        self.key = int.from_bytes(data[end_used_key_length:end_key], ENDIAN)

        start_after = end_used_key_length + KEY_BYTES
        end_after = end_key + PAGE_REFERENCE_BYTES
        self.after = int.from_bytes(data[start_after:end_after], ENDIAN)

    def dump(self) -> bytes:
        assert isinstance(self.before, int)
        assert isinstance(self.key, int)
        assert isinstance(self.after, int)

        key_as_bytes = self.key.to_bytes(KEY_BYTES, ENDIAN)
        used_key_length = len(key_as_bytes)

        data = (
            self.before.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN) +
            used_key_length.to_bytes(USED_VALUE_LENGTH_BYTES, ENDIAN) +
            key_as_bytes +
            bytes(KEY_BYTES - used_key_length) +
            self.after.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN)
        )
        return data

    def __repr__(self):
        return '<Reference: key={} before={} after={}>'.format(
            self.key, self.before, self.after
        )
