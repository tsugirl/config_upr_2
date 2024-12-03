import json
import os
import xml.etree.ElementTree as ET

def parse_dependencies(pom_path):
    """Парсинг зависимостей из POM-файла."""
    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}

    dependencies = []
    for dependency in root.findall(".//maven:dependency", ns):
        group_id = dependency.find("maven:groupId", ns).text
        artifact_id = dependency.find("maven:artifactId", ns).text
        dependencies.append(f"{group_id}:{artifact_id}")
    return dependencies

def generate_plantuml_graph(dependencies, output_path):
    """Генерация графа PlantUML."""
    with open(output_path, 'w') as file:
        file.write("@startuml\n")
        for dep in dependencies:
            file.write(f'"Root" --> "{dep}"\n')
        file.write("@enduml\n")
    print(f"Graph saved to {output_path}")

def main():
    # чтение конфигурационного файла
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    pom_path = config["pom_path"]
    output_path = config["output_path"]

    # парсинг зависимостей
    dependencies = parse_dependencies(pom_path)

    # генерация графа PlantUML
    generate_plantuml_graph(dependencies, output_path)

    # печать на экран
    with open(output_path, 'r') as file:
        print(file.read())

if __name__ == "__main__":
    main()
