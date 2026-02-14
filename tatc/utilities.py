from typing import Generator, Iterable, Sized, Union

import numbers
import re
import os


class Objects:
    @staticmethod
    def is_blank(value: any):
        """
        Returns true when the specified value is None or is a zero length collection or string..
        """
        if value is None:
            return True

        if isinstance(value, bool) or isinstance(value, numbers.Number):
            return False

        return not bool(value)


class Boolean:
    @staticmethod
    def parse(value: any) -> bool:
        """
        Parses and return true if the string matches 'true' or 'yes'; otherwise,
        returns true if not blank or non-zero
        """
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in ['true', 'yes']

        return bool(value)

    @staticmethod
    def to_string(value: bool):
        """
        Returns the lower case 'true' or 'false' associated to specified value.
        """
        if not isinstance(value, bool):
            raise TypeError
        # the programmer way, but somewhat unnecessary
        # return str(value).lower()
        return 'true' if value else 'false'


class String:
    def is_blank(value: str) -> bool:
        return Objects.is_blank(value.strip())

    @staticmethod
    def strips(values: Iterable[str]) -> list[str]:
        """
        Strips blank spaces from string values within an iterable
        """
        return [v.strip() for v in values]

    @staticmethod
    def try_split(value: Union[str, any], delimiter: str) -> Union[list[str], any]:
        """
        Tries to split the value into a list if the given value is a str type; otherwise, return value as it is.
        """
        if isinstance(value, str):
            return value.split(delimiter)
        return value

    @staticmethod
    def join(delimiter: str, values: Iterable[str], max_length: int = 0) -> Union[Generator[str, any, None], list[str]]:
        """
        Joins and returns the a collection of string, when each string is no longer than the specified max_length
        inclusive of the specified delimiter.
        """
        if not max_length:
            return [delimiter.join(values)]

        text = ''
        for value in values:
            if len(text) + len(value) + len(delimiter) <= max_length:
                text = f'{text}{delimiter}{value}' if text else value
                continue
            yield text
            text = value
        yield text


class Collections:
    @staticmethod
    def distinct(values: Iterable, remove_blanks: bool = False) -> list:
        """
        Returns the unique value similar to using set
        """
        unique = set(values)
        if remove_blanks:
            unique = filter(lambda x: not Objects.is_blank(x), values)
        return unique

    @staticmethod
    def split(values: Sized, size: int = 0) -> Generator[list, any, Sized]:
        """
        Returns the specified collection into a list of collections when each collection is no greater
        than the size specified
        """
        if not size:
            return values
        for i in range(0, len(values), size):
            yield list(values[i:i+size])


class Directory:
    def listdir(path: str, regex_filter: str = '.*') -> list[str]:
        path = os.path.abspath(path)
        names = list(filter(
            lambda name: re.match(regex_filter, name),
            os.listdir(path)
        ))
        return [os.path.join(path, name) for name in names]
