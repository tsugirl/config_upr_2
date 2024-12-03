import json
import os
import xml.etree.ElementTree as ET


def resolve_property(value, properties):
    if value and value.startswith("${") and value.endswith("}"):
        prop_name = value[2:-1]
        return properties.get(prop_name, value)
    return value


def parse_pom_file(pom_path, repository_path, processed=None, parent_properties=None, graph=None):
    if processed is None:
        processed = set()
    if parent_properties is None:
        parent_properties = {}
    if graph is None:
        graph = {}

    # проверка наличия POM-файла
    if not os.path.exists(pom_path):
        print(f"File not found: {pom_path}")
        return graph

    # парсинг POM-файла
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    except ET.ParseError as e:
        print(f"Error parsing {pom_path}: {e}")
        return graph

    # сбор свойств проекта
    properties = parent_properties.copy()
    for prop in root.findall(".//maven:properties/*", ns):
        properties[prop.tag.split("}")[-1]] = prop.text

    # разрешение версии проекта
    project_version = root.find("maven:version", ns)
    if project_version is not None:
        properties["project.version"] = project_version.text

    # проверка родительского POM
    parent = root.find(".//maven:parent", ns)
    if parent is not None:
        parent_group_id = parent.find("maven:groupId", ns)
        parent_artifact_id = parent.find("maven:artifactId", ns)
        parent_version = parent.find("maven:version", ns)

        if parent_group_id is not None and parent_artifact_id is not None and parent_version is not None:
            parent_pom_path = os.path.join(
                repository_path,
                parent_group_id.text.replace('.', '/'),
                parent_artifact_id.text,
                parent_version.text,
                f"{parent_artifact_id.text}-{parent_version.text}.pom"
            )

            # рекурсия для обработки родительского POM
            if os.path.exists(parent_pom_path):
                parse_pom_file(parent_pom_path, repository_path, processed, properties, graph)

    # установка groupId проекта
    project_group = root.find("maven:groupId", ns)
    if project_group is None and parent is not None:  # groupId отсутствует, беру из родителя
        project_group = parent.find("maven:groupId", ns)

    if project_group is not None:
        project_group = resolve_property(project_group.text, properties)
    else:
        project_group = "unknown"

    # установка artifactId проекта
    project_name = root.find("maven:artifactId", ns)
    if project_name is not None:
        project_name = resolve_property(project_name.text, properties)
    else:
        print(f"Missing artifactId in {pom_path}")
        return graph

    # разрешение версии проекта
    project_version = resolve_property(project_version.text if project_version is not None else "unspecified", properties)

    root_key = f"{project_group}:{project_name}:{project_version}"
    if root_key not in graph:
        graph[root_key] = []

    # парсинг зависимостей
    for dependency in root.findall(".//maven:dependency", ns):
        group_id = dependency.find("maven:groupId", ns)
        artifact_id = dependency.find("maven:artifactId", ns)
        version = dependency.find("maven:version", ns)

        if group_id is None or artifact_id is None:
            continue  # если какие-то нужные поля отсутствуют - пропускаю

        group_id = resolve_property(group_id.text, properties)
        artifact_id = resolve_property(artifact_id.text, properties)
        version = resolve_property(version.text if version is not None else "unspecified", properties)

        dependency_key = f"{group_id}:{artifact_id}:{version}"

        if dependency_key not in processed:
            processed.add(dependency_key)
            graph[root_key].append(dependency_key)

            # путь к POM-файлу (транзитивной) зависимости
            dependency_pom_path = os.path.join(
                repository_path,
                group_id.replace('.', '/'),
                artifact_id,
                version,
                f"{artifact_id}-{version}.pom"
            )

            # рекурсия обработки зависимостей
            if os.path.exists(dependency_pom_path):
                graph = parse_pom_file(dependency_pom_path, repository_path, processed, properties, graph)

    return graph



def generate_plantuml_graph(graph, output_path):
    with open(output_path, 'w') as file:
        file.write("@startuml\n")
        for node, dependencies in graph.items():
            for dep in dependencies:
                file.write(f'"{node}" --> "{dep}"\n')
        file.write("@enduml\n")
    print(f"Graph saved to {output_path}")


def main():
    # чтение конфигурационного файла
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    pom_path = config["pom_path"]
    output_path = config["output_path"]

    # указание пути к локальному Maven-репозиторию
    repository_path = os.path.expanduser("~/.m2/repository")

    # Ррекурсивный парсинг зависимостей
    graph = parse_pom_file(pom_path, repository_path)

    # генерация графа PlantUML
    generate_plantuml_graph(graph, output_path)

    # печать на экран
    with open(output_path, 'r') as file:
        print(file.read())


if __name__ == "__main__":
    main()
