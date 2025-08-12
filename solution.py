import argparse
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import xml.etree.ElementTree as ET
import json
from abc import ABC, abstractmethod


@dataclass
class Student:
    id: int
    name: str
    room_id: int


@dataclass
class Room:
    id: int
    name: str
    students: list[Student] = field(default_factory=list)


class DataLoader(ABC):
    """
    Abstract class serving as an interface for all data loading mechanisms
    """

    @abstractmethod
    def load(
        self, students_path: str, rooms_path: str
    ) -> tuple[list[Student], list[Room]]:
        pass


class DataSerializer(ABC):
    """
    Abstract class serving as an interface for all data serialization mechanisms
    """

    @abstractmethod
    def serialize(self, combined_rooms: list[Room]) -> str:
        pass


class JsonDataLoader(DataLoader):
    def load(
        self, students_path: str, rooms_path: str
    ) -> tuple[list[Student], list[Room]]:
        def load_json(path):
            with open(path) as f:
                return json.load(f)

        students_json = load_json(students_path)
        rooms_json = load_json(rooms_path)

        students = [Student(s["id"], s["name"], s["room"]) for s in students_json]
        rooms = [Room(r["id"], r["name"]) for r in rooms_json]

        return students, rooms


class XmlDataLoader(DataLoader):
    def load(
        self, students_path: str, rooms_path: str
    ) -> tuple[list[Student], list[Room]]:
        def parse_students(xml_path):
            try:
                tree = ET.parse(xml_path)
                students = []
                for student_el in tree.getroot():
                    student = Student(
                        id=int(student_el.find("id").text),
                        name=student_el.find("name").text,
                        room_id=int(student_el.find("room").text),
                    )
                    students.append(student)
                return students
            except ET.ParseError:
                raise ValueError(f"Error parsing XML file: {xml_path}")

        def parse_rooms(xml_path):
            try:
                tree = ET.parse(xml_path)
                rooms = []
                for room_el in tree.getroot():
                    room = Room(
                        id=int(room_el.find("id").text), name=room_el.find("name").text
                    )
                    rooms.append(room)
                return rooms
            except ET.ParseError:
                raise ValueError(f"Error parsing XML file: {xml_path}")

        students = parse_students(students_path)
        rooms = parse_rooms(rooms_path)
        return students, rooms


class JsonDataSerializer(DataSerializer):
    def serialize(self, combined_rooms: list[Room]) -> str:
        rooms_as_dictionary = [asdict(room) for room in combined_rooms]
        return json.dumps(rooms_as_dictionary, indent=4)


class XmlDataSerializer(DataSerializer):
    def serialize(self, combined_rooms: list[Room]) -> str:
        root = ET.Element("Rooms")

        for room in combined_rooms:
            sub_root = ET.SubElement(root, "Room")
            room_id = ET.SubElement(sub_root, "id")
            room_id.text = str(room.id)

            room_name = ET.SubElement(sub_root, "name")
            room_name.text = room.name

            room_students = ET.SubElement(sub_root, "Students")

            for student in room.students:
                student_el = ET.SubElement(room_students, "Student")

                student_id = ET.SubElement(student_el, "id")
                student_id.text = str(student.id)

                student_name = ET.SubElement(student_el, "name")
                student_name.text = student.name

                student_room = ET.SubElement(student_el, "room")
                student_room.text = str(student.room_id)
        return ET.tostring(root, encoding="unicode")


class RoomDataProcessor:
    """
    Class for primary business logic.
    """

    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def combine_rooms(self, students_path: str, rooms_path: str) -> list[Room]:
        students, rooms = self.data_loader.load(students_path, rooms_path)

        student_map = defaultdict(list)
        for student in students:
            student_map[student.room_id].append(student)

        for room in rooms:
            room.students = student_map.get(room.id, [])

        return rooms


def main():
    """
    Main function for parsing CLI arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("students_file", help="Path to student JSON file")
    parser.add_argument("rooms_file", help="Path to room JSON file")
    parser.add_argument(
        "-i",
        "--input-format",
        choices=["json", "xml"],
        default="json",
        help="Path to output JSON file",
    )
    parser.add_argument(
        "-o",
        "--output-format",
        choices=["json", "xml"],
        default="json",
        help="Path to output JSON file",
    )
    parser.add_argument(
        "-d",
        "--output-destination",
        help="Path to output file, if not specified, prints to console",
    )
    args = parser.parse_args()

    if args.input_format == "json":
        data_loader = JsonDataLoader()
    elif args.input_format == "xml":
        data_loader = XmlDataLoader()
    else:
        raise ValueError(f"Input format {args.input_format} is not supported")

    processor = RoomDataProcessor(data_loader)

    combined_rooms = processor.combine_rooms(args.students_file, args.rooms_file)

    if args.output_format == "json":
        serializer = JsonDataSerializer()
    elif args.output_format == "xml":
        serializer = XmlDataSerializer()
    else:
        raise ValueError(
            f"Output format {
                args.output_format} is not supported"
        )

    output_data = serializer.serialize(combined_rooms)

    if args.output_destination:
        with open(args.output_destination, "w") as f:
            f.write(output_data)
        print(f"Wrote to {args.output_destination} successfully!")
    else:
        print(output_data)


if __name__ == "__main__":
    main()
